# agent_factory/schema/tests/test_cli_lock.py
"""lock 命令组测试（真实 git 仓库）."""
import os
import subprocess
from pathlib import Path

import yaml
from click.testing import CliRunner

from agent_factory.cli import main

DEAD_PID = 999999  # 合法但几乎不会被分配的 pid（Linux pid_max 默认 4194304）


def _init_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True,
                   capture_output=True)


def _lock_dir(tmp_path: Path) -> Path:
    return tmp_path / ".git" / "locks" / "e2e.lock"


def _plant_lock(tmp_path: Path, holder: str, pid: int) -> None:
    """手工种一个锁（模拟他实例持有）."""
    d = _lock_dir(tmp_path)
    d.mkdir(parents=True)
    (d / "holder.yaml").write_text(yaml.safe_dump(
        {"holder": holder, "pid": pid, "since": "2026-09-22T10:00:00"},
        allow_unicode=True, sort_keys=False))


def test_lock_acquire_and_release(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_git(tmp_path)
    runner = CliRunner()

    r = runner.invoke(main, ["lock", "acquire", "e2e",
                             "--holder", "feature/001-x", "--pid", str(os.getpid())])
    assert r.exit_code == 0, r.output
    assert "Acquired e2e lock" in r.output
    assert _lock_dir(tmp_path).is_dir()

    r = runner.invoke(main, ["lock", "status", "e2e"])
    assert "held" in r.output and "feature/001-x" in r.output and "alive" in r.output

    r = runner.invoke(main, ["lock", "release", "e2e"])
    assert r.exit_code == 0 and "Released e2e lock" in r.output
    assert not _lock_dir(tmp_path).exists()

    r = runner.invoke(main, ["lock", "status", "e2e"])
    assert "free" in r.output


def test_lock_acquire_busy_when_holder_alive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_git(tmp_path)
    _plant_lock(tmp_path, "feature/002-y", os.getpid())  # 活进程持有
    runner = CliRunner()

    r = runner.invoke(main, ["lock", "acquire", "e2e",
                             "--holder", "feature/003-z", "--pid", str(os.getpid())])
    assert r.exit_code == 1
    assert "LockBusy" in r.output
    assert "feature/002-y" in r.output


def test_lock_acquire_cleans_stale_lock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_git(tmp_path)
    _plant_lock(tmp_path, "feature/002-y", DEAD_PID)  # 死进程残留锁
    runner = CliRunner()

    r = runner.invoke(main, ["lock", "acquire", "e2e",
                             "--holder", "feature/003-z", "--pid", str(os.getpid())])
    assert r.exit_code == 0, r.output
    assert "stale" in r.output
    # 新 holder 已写入
    data = yaml.safe_load((_lock_dir(tmp_path) / "holder.yaml").read_text())
    assert data["holder"] == "feature/003-z"


def test_lock_acquire_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_git(tmp_path)
    _plant_lock(tmp_path, "feature/002-y", os.getpid())  # 活锁也强取
    runner = CliRunner()

    r = runner.invoke(main, ["lock", "acquire", "e2e", "--force",
                             "--holder", "feature/003-z", "--pid", str(os.getpid())])
    assert r.exit_code == 0, r.output
    assert "强制清除" in r.output
    data = yaml.safe_load((_lock_dir(tmp_path) / "holder.yaml").read_text())
    assert data["holder"] == "feature/003-z"


def test_lock_release_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_git(tmp_path)
    runner = CliRunner()

    r = runner.invoke(main, ["lock", "release", "e2e"])
    assert r.exit_code == 0
    assert "No e2e lock held" in r.output
