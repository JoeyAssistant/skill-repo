# agent_factory/cli/feature.py
"""feature command group."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from agent_factory.cli.common import (
    dump_yaml, find_feature_dir, format_error, load_yaml, next_feature_id,
)
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import FeatureStatus


def _feature_doc() -> str:
    """读 doc/feature.md 原文作为 group help（设计文档 = help 唯一真值）.

    click 会对 help 文本按段落 rewrap（换行被压扁）；在每个段落前插 \\b
    标记可让该段原样输出，保留 feature.md 的原始换行。
    """
    p = Path(__file__).resolve().parent.parent / "doc" / "feature.md"
    if not p.exists():
        return "Operate feature FEATURE.yaml."
    return "\n\b\n" + p.read_text().replace("\n\n", "\n\n\b\n")


@click.group("feature", help=_feature_doc())
def feature_group() -> None:
    """Operate feature FEATURE.yaml."""


@feature_group.command("new")
@click.option("--title", required=True, help="Human-readable title")
@click.option("--slug", required=True, help="Directory slug (kebab-case)")
@click.option("--user-input", required=True, help="User's original request input (preserved verbatim)")
@click.option(
    "--priority",
    type=click.Choice([p.value for p in Priority]),
    default=Priority.P2.value,
    help="Priority (default: P2)",
)
@click.option("--summary", default=None,
              help="一句话总结（≤50 字）：以「支持 xxx / 解决 xxx」开头（后续可用 feature set 补）")
def new(title: str, slug: str, user_input: str, priority: str,
        summary: str | None) -> None:
    """Create new feature (status=draft).

    Directory name: <NNN>-<slug> (e.g., 001-income-module).
    Both FEATURE.yaml 'title' field and index 'title' field use the directory name.
    """
    import re
    if not re.match(r"^[a-z][a-z0-9-]*$", slug):
        click.echo(format_error(
            "InvalidSlug",
            f"Slug must be kebab-case (lowercase letters/digits/hyphens): {slug}",
            None,
        ), err=True)
        sys.exit(4)

    feature_id = next_feature_id()
    dir_name = f"{feature_id:03d}-{slug}"
    feature_dir = Path(".features") / dir_name
    if feature_dir.exists():
        click.echo(format_error("FileExists", f"Directory already exists: {feature_dir}", str(feature_dir)), err=True)
        sys.exit(1)

    # Build Feature object (validates immediately)
    try:
        feature = Feature(
            id=feature_id,
            title=dir_name,  # title field = directory name
            user_input=user_input,
            summary=summary,
        )
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), None), err=True)
        sys.exit(1)

    # Create directory + FEATURE.yaml
    feature_dir.mkdir(parents=True)
    feat_path = feature_dir / "FEATURE.yaml"
    dump_yaml(feat_path, feature)

    # Update index.yaml
    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path)) if idx_path.exists() else FeatureIndex()
    idx.features.append(FeatureIndexItem(
        id=feature_id,
        title=dir_name,  # index title = directory name
        status=FeatureStatus.DRAFT,
        priority=Priority(priority),
    ))
    dump_yaml(idx_path, idx)

    click.echo(f"Created feature {feature_id}: {dir_name}")


# Fields that route to FEATURE.yaml (plain scalars)
SCALAR_FIELDS = {"user_input", "summary", "source_issue"}

# Subfields of background that can be set individually
BACKGROUND_SUBFIELDS = {"pain_point", "benefit"}


@feature_group.command("set")
@click.argument("feature_id", type=int)
@click.argument("field")
@click.argument("value", required=False)
@click.option("--file", "file_path", type=click.Path(exists=True, path_type=Path),
              help="Read value from file")
@click.option("--remove", is_flag=False, flag_value=True, default=False,
              help="Delete spec.<module>（仅对 spec.<module> 路径生效）")
def set_field(feature_id: int, field: str, value: str | None,
              file_path: Path | None, remove: bool) -> None:
    """Update FEATURE.yaml. 支持嵌套路径：background.pain_point / spec.<module>

    传值约定：多行长文本（user_input / background / spec 等）统一 `--file <path>` 传值——
    inline 传参在含引号 / $ / 反引号 / # 时 shell 转义不可靠，内容会静默截断或损坏；
    --file 原样读入零转义。
    """
    # --- parse field path ---
    head, _, sub = field.partition(".")

    # spec.<module> path
    if head == "spec":
        if not sub:
            _invalid_field(field)
        if "." in sub:
            _invalid_field(field)  # field-level spec paths like spec.income.functions NOT supported
        module = sub
        if remove:
            _spec_remove(feature_id, module); return
        if not file_path:
            click.echo(format_error("InvalidArgs",
                f"spec.{module} 需要 --file <path>（ModuleSpec yaml）或 --remove", None), err=True)
            sys.exit(4)
        _spec_upsert(feature_id, module, file_path); return

    # --remove only valid for spec.<module>
    if remove:
        click.echo(format_error("InvalidArgs", "--remove 仅对 spec.<module> 生效", None), err=True)
        sys.exit(4)

    # Plain scalar fields
    if head in SCALAR_FIELDS and not sub:
        new_value = _read_value(value, file_path)
        _set_plain(feature_id, head, new_value); return

    # Background paths
    if head == "background":
        if sub in BACKGROUND_SUBFIELDS:
            new_value = _read_value(value, file_path)
            _set_background_sub(feature_id, sub, new_value); return
        if not sub:
            if not file_path:
                click.echo(format_error("InvalidArgs",
                    "background 整体写入需 --file（yaml: {pain_point, benefit}）", None), err=True)
                sys.exit(4)
            _set_background_whole(feature_id, file_path); return

    # e2e_test_cases whole list
    if field == "e2e_test_cases":
        if not file_path:
            click.echo(format_error("InvalidArgs",
                "e2e_test_cases 整列表替换需 --file（yaml: list of {name, precondition, inputs, steps, observations[{check, expect}], cleanup}；cleanup 为非空步骤列表或 \"N/A\"）",
                None), err=True)
            sys.exit(4)
        _set_e2e_test_cases(feature_id, file_path); return

    # deploy whole list
    if field == "deploy":
        if not file_path:
            click.echo(format_error("InvalidArgs",
                "deploy 整列表替换需 --file（yaml: list of str，一条一行；无上线变更写 []）",
                None), err=True)
            sys.exit(4)
        _set_deploy(feature_id, file_path); return

    _invalid_field(field)


def _read_value(value: str | None, file_path: Path | None) -> str:
    """Read value from --file or inline argument."""
    if file_path:
        return file_path.read_text()
    if value is not None:
        return value
    click.echo(format_error("MissingValue", "Either VALUE or --file required", None), err=True)
    sys.exit(4)


def _invalid_field(field: str) -> None:
    """Exit with invalid field error."""
    click.echo(format_error("InvalidField",
        f"Field '{field}' not supported. 合法形式：user_input / source_issue / background "
        f"/ background.pain_point / background.benefit / spec.<module> / e2e_test_cases / deploy",
        None), err=True)
    sys.exit(4)


def _load_feature(feature_id: int) -> tuple[Path, dict]:
    """Load feature FEATURE.yaml, returning (path, data dict)."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)
    path = feature_dir / "FEATURE.yaml"
    return path, load_yaml(path)


def _save(feature_id: int, path: Path, data: dict) -> None:
    """Validate and save feature data."""
    try:
        feature = Feature.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(path)), err=True)
        sys.exit(1)
    dump_yaml(path, feature)
    click.echo(f"Updated feature {feature_id}")


def _set_plain(feature_id: int, key: str, new_value: str) -> None:
    path, data = _load_feature(feature_id)
    data[key] = new_value
    _save(feature_id, path, data)


def _set_background_sub(feature_id: int, sub: str, new_value: str) -> None:
    path, data = _load_feature(feature_id)
    bg = data.get("background") or {}
    bg[sub] = new_value
    data["background"] = bg
    _save(feature_id, path, data)


def _set_background_whole(feature_id: int, file_path: Path) -> None:
    path, data = _load_feature(feature_id)
    data["background"] = yaml.safe_load(file_path.read_text())
    _save(feature_id, path, data)


def _spec_upsert(feature_id: int, module: str, file_path: Path) -> None:
    path, data = _load_feature(feature_id)
    spec = data.get("spec") or {}
    spec[module] = yaml.safe_load(file_path.read_text())
    data["spec"] = spec
    _save(feature_id, path, data)


def _spec_remove(feature_id: int, module: str) -> None:
    path, data = _load_feature(feature_id)
    spec = data.get("spec") or {}
    if module not in spec:
        click.echo(format_error("NotFound", f"spec.{module} 不存在", None), err=True)
        sys.exit(2)
    del spec[module]
    data["spec"] = spec
    _save(feature_id, path, data)


def _validate_e2e_cleanup(cases: list) -> list[str]:
    """每条 E2E 用例必须声明非空 cleanup（防测试产物残留）。"""
    if not isinstance(cases, list):
        return ["e2e_test_cases 必须是列表"]
    issues = []
    for i, tc in enumerate(cases, 1):
        if isinstance(tc, dict):
            cleanup, name = tc.get("cleanup"), tc.get("name")
        else:
            cleanup, name = getattr(tc, "cleanup", None), getattr(tc, "name", None)
        if cleanup == "N/A":
            continue
        if not isinstance(cleanup, list) or not any(
            isinstance(item, str) and item.strip() for item in cleanup
        ):
            issues.append(
                f"e2e_test_cases[{i}]（{name or f'#{i}'}）cleanup 为空："
                f"必须声明清理步骤，或写 \"N/A\"（不需要/不涉及）")
    return issues


def _set_e2e_test_cases(feature_id: int, file_path: Path) -> None:
    path, data = _load_feature(feature_id)
    cases = yaml.safe_load(file_path.read_text())
    issues = _validate_e2e_cleanup(cases)
    if issues:
        click.echo(format_error("ValidationError", "; ".join(issues), str(file_path)), err=True)
        sys.exit(1)
    data["e2e_test_cases"] = cases
    _save(feature_id, path, data)


def _validate_deploy(items) -> list[str]:
    """deploy 必须是字符串列表，每条非空（防占位式空条目）。"""
    if not isinstance(items, list):
        return ["deploy 必须是字符串列表（无上线变更写 []）"]
    issues = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, str) or not item.strip():
            issues.append(f"deploy[{i}] 必须是非空字符串")
    return issues


def _set_deploy(feature_id: int, file_path: Path) -> None:
    path, data = _load_feature(feature_id)
    items = yaml.safe_load(file_path.read_text())
    if items is None:
        items = []
    issues = _validate_deploy(items)
    if issues:
        click.echo(format_error("ValidationError", "; ".join(issues), str(file_path)), err=True)
        sys.exit(1)
    data["deploy"] = items
    _save(feature_id, path, data)


@feature_group.command("show")
@click.argument("feature_id", type=int)
@click.option("--format", "fmt", type=click.Choice(["markdown", "yaml", "json"]), default="markdown")
def show(feature_id: int, fmt: str) -> None:
    """Show feature details."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    reqs_path = feature_dir / "FEATURE.yaml"
    data = load_yaml(reqs_path)
    feature = Feature.model_validate(data)

    if fmt == "json":
        click.echo(json.dumps(feature.model_dump(mode="json"), ensure_ascii=False, indent=2))
    elif fmt == "yaml":
        click.echo(yaml.safe_dump(feature.model_dump(mode="json"), allow_unicode=True, sort_keys=False))
    else:  # markdown
        click.echo(_render_feature_markdown(feature))


def _children_rollup(children: list[int]) -> list[str]:
    """Render children rollup table (status/priority read from index.yaml)."""
    idx_path = Path(".features") / "index.yaml"
    by_id: dict[int, FeatureIndexItem] = {}
    if idx_path.exists():
        idx = FeatureIndex.model_validate(load_yaml(idx_path))
        by_id = {i.id: i for i in idx.features}
    lines = ["## Children", "", "| ID | STATUS | PRIORITY | TITLE |", "|---|---|---|---|"]
    for cid in children:
        item = by_id.get(cid)
        if item is None:
            lines.append(f"| {cid} | (未在 index) | - | - |")
        else:
            lines.append(f"| {cid} | {item.status.value} | {item.priority.value} | {item.title} |")
    lines.append("")
    return lines


def _render_feature_markdown(feature: Feature) -> str:
    lines = [
        f"# Feature {feature.id}: {feature.title}",
        "",
    ]
    if feature.summary:
        lines += [f"**Summary**: {feature.summary}", ""]
    lines += [
        f"**User Input**: {feature.user_input}",
        "",
    ]
    if feature.parent is not None:
        lines += [f"**Parent**: feature #{feature.parent}", ""]
    if feature.children:
        lines += _children_rollup(feature.children)
    if feature.worktree:
        lines += [
            f"**Worktree**: {feature.worktree.path} (branch: {feature.worktree.branch})",
            "",
        ]
    if feature.background:
        lines += [
            "## Background",
            f"**痛点**: {feature.background.pain_point}",
            f"**收益**: {feature.background.benefit}",
            "",
        ]
    if feature.spec:
        for module_name, module_spec in feature.spec.items():
            lines += [f"## Spec — {module_name}", ""]
            if module_spec.functions:
                lines.append("**Functions**:")
                for i, fn in enumerate(module_spec.functions, 1):
                    lines.append(f"{i}. {fn}")
                lines.append("")
    if feature.e2e_test_cases:
        lines.append("## E2E Test Cases")
        lines.append("")
        for tc in feature.e2e_test_cases:
            lines += [
                f"### {tc.name}",
                f"- **precondition**: {tc.precondition}",
                f"- **inputs**: {json.dumps(tc.inputs, ensure_ascii=False) if tc.inputs else '-'}",
                "",
                "**steps**:",
            ]
            for i, step in enumerate(tc.steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
            lines.append("**observations**:")
            if tc.observations:
                for j, obs in enumerate(tc.observations, 1):
                    lines += [f"  {j}. `{obs.check}` → **expect**: {obs.expect}"]
            else:
                lines.append("  无")
            lines.append("")
            lines.append("**cleanup**:")
            if tc.cleanup == "N/A":
                lines.append("  N/A（不需要/不涉及清理）")
            elif tc.cleanup:
                for k, step in enumerate(tc.cleanup, 1):
                    lines.append(f"  {k}. {step}")
            else:
                lines.append("  无")
            lines.append("")
    if feature.deploy:
        lines += ["## Deploy", ""]
        for i, item in enumerate(feature.deploy, 1):
            lines.append(f"{i}. {item}")
        lines.append("")
    return "\n".join(lines)


def _summary_for(title: str) -> str | None:
    """从 FEATURE.yaml 读取 summary（index 不维护 summary，避免双写）。"""
    path = Path(".features") / title / "FEATURE.yaml"
    if not path.exists():
        return None
    try:
        data = load_yaml(path)
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("summary")
    return value if isinstance(value, str) else None


@feature_group.command("list")
@click.option("--status", type=click.Choice([s.value for s in FeatureStatus]), help="Filter by status")
@click.option("--priority", type=click.Choice([p.value for p in Priority]), help="Filter by priority")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_features(status: str | None, priority: str | None, fmt: str) -> None:
    """List features."""
    idx_path = Path(".features") / "index.yaml"
    if not idx_path.exists():
        click.echo("No features found.")
        return

    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    items = idx.features
    if status:
        items = [i for i in items if i.status.value == status]
    if priority:
        items = [i for i in items if i.priority.value == priority]

    summaries = {item.id: _summary_for(item.title) for item in items}

    if fmt == "json":
        rows = []
        for item in items:
            row = item.model_dump(mode="json")
            row["summary"] = summaries[item.id]
            rows.append(row)
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'ID':<5} {'STATUS':<15} {'PRIORITY':<10} {'TITLE':<45} SUMMARY")
        for item in items:
            summary = summaries[item.id] or "-"
            click.echo(f"{item.id:<5} {item.status.value:<15} {item.priority.value:<10} {item.title:<45} {summary}")


# State machine: allowed transitions
ALLOWED_TRANSITIONS = {
    FeatureStatus.DRAFT: {FeatureStatus.DESIGNING, FeatureStatus.CANCELLED},
    FeatureStatus.DESIGNING: {FeatureStatus.APPROVED, FeatureStatus.CANCELLED},
    FeatureStatus.APPROVED: {FeatureStatus.IMPLEMENTING, FeatureStatus.CANCELLED},
    FeatureStatus.IMPLEMENTING: {FeatureStatus.QA_REVIEWING},
    FeatureStatus.QA_REVIEWING: {FeatureStatus.DONE, FeatureStatus.IMPLEMENTING},  # QA fail → implementing
    FeatureStatus.DONE: set(),
    FeatureStatus.CANCELLED: set(),
}


def _validate_transition_requirements(current: FeatureStatus, target: FeatureStatus, feature: Feature) -> list[str]:
    """Return list of missing requirements for transition (empty = OK)."""
    issues = []
    if current == FeatureStatus.DRAFT and target == FeatureStatus.DESIGNING:
        bg = feature.background
        if not bg or not (bg.pain_point or "").strip():
            issues.append("background.pain_point is empty")
        if not bg or not (bg.benefit or "").strip():
            issues.append("background.benefit is empty")
    elif current == FeatureStatus.DESIGNING and target == FeatureStatus.APPROVED:
        if not feature.spec:
            issues.append("spec is empty（至少 1 个模块）")
        # e2e_test_cases 可为空（无 E2E 场景的需求）；非空时每条用例必须声明 cleanup
        issues.extend(_validate_e2e_cleanup(feature.e2e_test_cases))
    # approved→implementing: no check (decisions removed)
    return issues


@feature_group.command("transition")
@click.argument("feature_id", type=int)
@click.option("--to", "target", required=True, type=click.Choice([s.value for s in FeatureStatus]))
def transition(feature_id: int, target: str) -> None:
    """Transition feature status (with cross-field validation).

    Cross-field checks:
    - draft → designing: background.pain_point + benefit must be non-empty
    - designing → approved: spec >= 1 module（e2e_test_cases 可为空；非空时每条用例 cleanup 必填非空）
    - approved → implementing: no extra check
    """
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    target_status = FeatureStatus(target)

    # Load current status from index
    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    current_item = next((i for i in idx.features if i.id == feature_id), None)
    if not current_item:
        click.echo(format_error("NotFound", f"Feature {feature_id} not in index", None), err=True)
        sys.exit(2)

    current_status = current_item.status

    # Validate path
    if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        click.echo(format_error(
            "InvalidTransition",
            f"Path '{current_status.value} → {target_status.value}' is not allowed",
            None,
        ), err=True)
        sys.exit(3)

    # Cross-field validation (load FEATURE.yaml)
    reqs_path = feature_dir / "FEATURE.yaml"
    feature = Feature.model_validate(load_yaml(reqs_path))
    issues = _validate_transition_requirements(current_status, target_status, feature)
    if issues:
        click.echo(format_error(
            "ValidationError",
            f"Cannot transition to {target_status.value}: " + "; ".join(issues),
            str(reqs_path),
        ), err=True)
        sys.exit(1)

    # Update index
    current_item.status = target_status
    dump_yaml(idx_path, idx)

    click.echo(f"Transitioned feature {feature_id}: {current_status.value} → {target_status.value}")


@feature_group.command("delete")
@click.argument("feature_id", type=int)
@click.option("--force", is_flag=True, help="Required to actually delete (no interactive confirm)")
def delete(feature_id: int, force: bool) -> None:
    """Delete feature (directory + index entry)."""
    if not force:
        click.echo(format_error("ForceRequired", "Pass --force to confirm deletion", None), err=True)
        sys.exit(1)

    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    # Remove directory
    shutil.rmtree(feature_dir)

    # Remove from index
    idx_path = Path(".features") / "index.yaml"
    if idx_path.exists():
        idx = FeatureIndex.model_validate(load_yaml(idx_path))
        idx.features = [i for i in idx.features if i.id != feature_id]
        dump_yaml(idx_path, idx)

    click.echo(f"Deleted feature {feature_id}")
