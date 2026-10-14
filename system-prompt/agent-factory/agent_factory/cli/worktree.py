# agent_factory/cli/worktree.py
"""worktree command group - feature 绑定的 git worktree 生命周期管理.

约定：
- worktree 目录：.worktrees/feat-<NNN>-<slug>（.gitignore 忽略）
- 分支：feature/<NNN>-<slug>
- 绑定记录写入 FEATURE.yaml worktree 字段（name/branch/path）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
from pydantic import ValidationError

from agent_factory.cli.common import (
    dump_yaml, find_feature_dir, format_error, load_yaml,
)
from agent_factory.schema import Feature, FeatureIndex
from agent_factory.schema.feature import FeatureStatus

WORKTREES_DIR = ".worktrees"


def _worktree_doc() -> str:
    """读 doc/worktree.md 原文作为 group help（设计文档 = help 唯一真值）."""
    p = Path(__file__).resolve().parent.parent / "doc" / "worktree.md"
    if not p.exists():
        return "Manage git worktrees bound to features."
    return "\n\b\n" + p.read_text().replace("\n\n", "\n\n\b\n")


@click.group("worktree", help=_worktree_doc())
def worktree_group() -> None:
    """Manage git worktrees bound to features."""


def _git(*args: str) -> subprocess.CompletedProcess:
    """Run git command, return CompletedProcess (never raises)."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def _branch_exists(branch: str) -> bool:
    """分支是否存在于本地（remove 幂等：PR 合入后平台删源分支时跳过删除）。"""
    return bool(_git("branch", "--list", branch).stdout.strip())


def _git_fail(result: subprocess.CompletedProcess, context: str) -> None:
    """Print git stderr and exit 1."""
    click.echo(format_error("GitError", result.stderr.strip() or result.stdout.strip(), context), err=True)
    sys.exit(1)


def _load_feature_with_worktree(feature_id: int) -> tuple[Path, Path, Feature]:
    """Load feature; return (feature_dir, feat_yaml_path, Feature)."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)
    feat_path = feature_dir / "FEATURE.yaml"
    try:
        feature = Feature.model_validate(load_yaml(feat_path))
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(feat_path)), err=True)
        sys.exit(1)
    return feature_dir, feat_path, feature


@worktree_group.command("new")
@click.argument("feature_id", type=int)
@click.option("--base", default="HEAD",
              help="基线分支（默认 HEAD；PM 流程传用户确认的基线分支，如 origin/dev）")
def new(feature_id: int, base: str) -> None:
    """为 feature 创建 worktree + 分支，并把绑定记录写入 FEATURE.yaml.

    目录 .worktrees/feat-<NNN>-<slug>，分支 feature/<NNN>-<slug>。
    """
    feature_dir, feat_path, feature = _load_feature_with_worktree(feature_id)

    if feature.worktree:
        click.echo(format_error(
            "AlreadyBound",
            f"Feature {feature_id} 已绑定 worktree: {feature.worktree.path} (branch: {feature.worktree.branch})",
            "如需重建，先 worktree remove",
        ), err=True)
        sys.exit(1)

    dir_name = feature_dir.name  # e.g. 002-income-module
    name = f"feat-{dir_name}"
    branch = f"feature/{dir_name}"
    path = Path(WORKTREES_DIR) / name

    r = _git("worktree", "add", str(path), "-b", branch, base)
    if r.returncode != 0:
        _git_fail(r, f"git worktree add {path} -b {branch} {base}")

    # 写 FEATURE.yaml worktree 记录（相对路径，不含 ./ 前缀；base 记基线分支）
    data = load_yaml(feat_path)
    data["worktree"] = {"name": name, "branch": branch, "path": str(path), "base": base}
    try:
        validated = Feature.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(feat_path)), err=True)
        sys.exit(1)
    dump_yaml(feat_path, validated)

    click.echo(f"Created worktree: {path} (branch: {branch}, base: {base})")


@worktree_group.command("list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_worktrees(fmt: str) -> None:
    """列出 git worktree 与 feature 绑定记录的对照（纯数据输出，异常判断留给 PM）.

    输出两节：
    - git worktree list：git 实际登记的 worktree（含主仓），标注绑定的 feature
    - feature 记录：FEATURE.yaml 里有 worktree 记录的 feature，标注目录是否在 git 登记中
    """
    import json as json_mod

    r = _git("worktree", "list", "--porcelain")
    if r.returncode != 0:
        _git_fail(r, "git worktree list --porcelain")

    # Parse porcelain: blocks of "worktree <path>" / "HEAD <sha>" / "branch <ref>"
    git_trees: list[dict] = []
    current: dict = {}
    for line in r.stdout.splitlines():
        if line.startswith("worktree "):
            if current:
                git_trees.append(current)
            current = {"path": line[len("worktree "):]}
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):].removeprefix("refs/heads/")
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):][:8]
    if current:
        git_trees.append(current)

    # feature 绑定记录：branch -> feature_id
    bindings: dict[str, int] = {}
    records: list[dict] = []
    features_dir = Path(".features")
    if features_dir.exists():
        for feat_yaml in sorted(features_dir.glob("*/FEATURE.yaml")):
            data = load_yaml(feat_yaml)
            wt = data.get("worktree")
            if wt:
                fid = data.get("id")
                bindings[wt.get("branch", "")] = fid
                records.append({
                    "id": fid,
                    "name": wt.get("name"),
                    "branch": wt.get("branch"),
                    "path": wt.get("path"),
                    "base": wt.get("base"),
                })

    # git worktree 绝对路径集合（用于判断记录中的 path 是否仍登记）
    git_paths = {str(Path(t["path"]).resolve()) for t in git_trees}
    for rec in records:
        rec["registered"] = str(Path(rec["path"]).resolve()) in git_paths

    if fmt == "json":
        click.echo(json_mod.dumps({"worktrees": git_trees, "records": records},
                                  ensure_ascii=False, indent=2))
        return

    click.echo("== git worktree list ==")
    for t in git_trees:
        branch = t.get("branch", "(detached)")
        fid = bindings.get(branch)
        bind = f"  -> feature #{fid}" if fid is not None else ""
        click.echo(f"{t['path']}  [{branch}]{bind}")

    click.echo("")
    click.echo("== feature worktree 记录 ==")
    if not records:
        click.echo("(无)")
    for rec in records:
        mark = "ok" if rec["registered"] else "MISSING(目录未在 git 登记)"
        base = f"  base={rec['base']}" if rec.get("base") else ""
        click.echo(f"feature #{rec['id']}  {rec['path']}  [{rec['branch']}]{base}  {mark}")


@worktree_group.command("remove")
@click.argument("feature_id", type=int)
@click.option("--force", is_flag=True,
              help="跳过 done 状态校验；git worktree remove --force；分支用 -D 强删")
def remove(feature_id: int, force: bool) -> None:
    """移除 feature 绑定的 worktree（校验 done）+ 删除分支 + 清 FEATURE.yaml 记录.

    正常路径（QA pass → 合入完成，merge 或 PR 已合入）后调用。worktree 有未提交改动或
    未跟踪文件时 git 会拒绝删除，确认无价值后用 --force。分支已不存在（如 PR 合入后
    平台删除源分支）时跳过删除，不报错。
    """
    _, feat_path, feature = _load_feature_with_worktree(feature_id)

    if not feature.worktree:
        click.echo(format_error("NotFound", f"Feature {feature_id} 无 worktree 绑定记录", None), err=True)
        sys.exit(2)

    # done 状态校验（从 index.yaml）
    if not force:
        idx_path = Path(".features") / "index.yaml"
        idx = FeatureIndex.model_validate(load_yaml(idx_path)) if idx_path.exists() else FeatureIndex()
        item = next((i for i in idx.features if i.id == feature_id), None)
        if item and item.status != FeatureStatus.DONE:
            click.echo(format_error(
                "InvalidTransition",
                f"Feature {feature_id} 状态为 {item.status.value}（非 done），拒绝移除 worktree",
                "确认要删用 --force",
            ), err=True)
            sys.exit(3)

    wt = feature.worktree
    path = Path(wt.path)

    # git worktree remove（目录不存在时先 prune 再跳过）
    if path.exists():
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(path))
        r = _git(*args)
        if r.returncode != 0:
            _git_fail(r, f"git worktree remove {path}（有改动或未跟踪文件时可确认后 --force）")
    else:
        click.echo(f"Note: worktree 目录不存在，跳过 remove: {path}", err=True)
        _git("worktree", "prune")

    # 删分支（-d 安全删除，--force 用 -D）；分支已不存在（平台删源分支 / 本地已 prune）视为已清理
    if _branch_exists(wt.branch):
        r = _git("branch", "-D" if force else "-d", wt.branch)
        if r.returncode != 0:
            _git_fail(r, f"git branch -d {wt.branch}（分支未合并时 -d 拒绝；确认后 --force 走 -D）")
    else:
        click.echo(f"Note: 分支 {wt.branch} 不存在，跳过删除", err=True)

    # 清 FEATURE.yaml worktree 记录
    data = load_yaml(feat_path)
    data["worktree"] = None
    dump_yaml(feat_path, Feature.model_validate(data))

    click.echo(f"Removed worktree: {wt.path} (branch deleted: {wt.branch})")
