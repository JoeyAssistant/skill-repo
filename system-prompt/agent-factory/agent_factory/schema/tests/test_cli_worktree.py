# agent_factory/schema/tests/test_cli_worktree.py
"""worktree 命令组测试（真实 git 仓库）."""
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"git {' '.join(args)} failed: {r.stderr}"
    return r


def _init_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "--allow-empty", "-m", "init")
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")


def _new_feature(runner: CliRunner) -> None:
    result = runner.invoke(main, [
        "feature", "new", "--title", "收入", "--slug", "income-module",
        "--user-input", "测试",
    ])
    assert result.exit_code == 0, result.output


def _set_status_done(tmp_path: Path) -> None:
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n"
        "- id: 1\n"
        "  title: 001-income-module\n"
        "  status: done\n"
        "  priority: P2\n")


def test_worktree_new_creates_dir_branch_and_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)

    result = runner.invoke(main, ["worktree", "new", "1"])
    assert result.exit_code == 0, result.output
    assert "Created worktree: .worktrees/feat-001-income-module" in result.output
    assert "feature/001-income-module" in result.output

    # 目录与分支存在
    assert (tmp_path / ".worktrees" / "feat-001-income-module").is_dir()
    branches = _git(tmp_path, "branch", "--list").stdout
    assert "feature/001-income-module" in branches

    # FEATURE.yaml 记录写入（未传 --base 时基线分支为 HEAD）
    data = load_yaml(tmp_path / ".features" / "001-income-module" / "FEATURE.yaml")
    assert data["worktree"] == {
        "name": "feat-001-income-module",
        "branch": "feature/001-income-module",
        "path": ".worktrees/feat-001-income-module",
        "base": "HEAD",
    }


def test_worktree_new_records_base_branch(tmp_path, monkeypatch):
    """基线分支随 --base 落库，便于会话中断后回溯 worktree 从何分出。"""
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    _git(tmp_path, "update-ref", "refs/remotes/origin/dev", "HEAD")
    runner = CliRunner()
    _new_feature(runner)

    result = runner.invoke(main, ["worktree", "new", "1", "--base", "origin/dev"])
    assert result.exit_code == 0, result.output

    data = load_yaml(tmp_path / ".features" / "001-income-module" / "FEATURE.yaml")
    assert data["worktree"]["base"] == "origin/dev"


def test_worktree_new_rejects_duplicate_binding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)

    assert runner.invoke(main, ["worktree", "new", "1"]).exit_code == 0
    result = runner.invoke(main, ["worktree", "new", "1"])
    assert result.exit_code == 1
    assert "AlreadyBound" in result.output


def test_worktree_list_shows_binding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)
    runner.invoke(main, ["worktree", "new", "1"])

    result = runner.invoke(main, ["worktree", "list"])
    assert result.exit_code == 0, result.output
    assert "feature/001-income-module" in result.output
    assert "-> feature #1" in result.output
    assert "ok" in result.output


def test_worktree_remove_rejects_non_done(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)
    runner.invoke(main, ["worktree", "new", "1"])

    result = runner.invoke(main, ["worktree", "remove", "1"])
    assert result.exit_code == 3
    assert "非 done" in result.output
    # worktree 与分支仍在
    assert (tmp_path / ".worktrees" / "feat-001-income-module").is_dir()


def test_worktree_remove_done_cleans_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)
    runner.invoke(main, ["worktree", "new", "1"])
    _set_status_done(tmp_path)

    result = runner.invoke(main, ["worktree", "remove", "1"])
    assert result.exit_code  == 0, result.output
    assert "Removed worktree" in result.output

    # 目录删除、分支删除、记录清除
    assert not (tmp_path / ".worktrees" / "feat-001-income-module").exists()
    branches = _git(tmp_path, "branch", "--list").stdout
    assert "feature/001-income-module" not in branches
    data = load_yaml(tmp_path / ".features" / "001-income-module" / "FEATURE.yaml")
    assert data["worktree"] is None


def test_worktree_remove_tolerates_missing_branch(tmp_path, monkeypatch):
    """PR 合入后平台删源分支：本地分支已不存在，remove 仍成功且清记录。"""
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)
    runner.invoke(main, ["worktree", "new", "1"])
    _set_status_done(tmp_path)

    # 模拟分支已被删除（平台删源分支 + 本地 prune）
    _git(tmp_path, "worktree", "remove", "--force", ".worktrees/feat-001-income-module")
    _git(tmp_path, "branch", "-D", "feature/001-income-module")

    result = runner.invoke(main, ["worktree", "remove", "1"])
    assert result.exit_code == 0, result.output
    data = load_yaml(tmp_path / ".features" / "001-income-module" / "FEATURE.yaml")
    assert data["worktree"] is None


def test_worktree_remove_without_record_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_repo(tmp_path)
    runner = CliRunner()
    _new_feature(runner)

    result = runner.invoke(main, ["worktree", "remove", "1"])
    assert result.exit_code == 2
    assert "无 worktree 绑定记录" in result.output
