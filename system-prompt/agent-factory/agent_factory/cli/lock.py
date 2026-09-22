# agent_factory/cli/lock.py
"""lock command group - 跨实例互斥锁（当前用于 E2E 验收串行）.

锁位置：$(git rev-parse --git-common-dir)/locks/<name>.lock/
所有 worktree 共享同一 git common dir，因此该路径是跨实例唯一全局点。

锁形态：目录（mkdir 原子操作）+ 内嵌 holder.yaml {holder, pid, since}。
stale 检测：acquire 失败时按 pid 做 kill -0 存活检查，死锁残留自动清理重取。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
import yaml

from agent_factory.cli.common import format_error

LOCKS_SUBDIR = "locks"
HOLDER_FILE = "holder.yaml"


def _lock_doc() -> str:
    """读 doc/lock.md 原文作为 group help（设计文档 = help 唯一真值）."""
    p = Path(__file__).resolve().parent.parent / "doc" / "lock.md"
    if not p.exists():
        return "Cross-instance mutual exclusion locks."
    return "\n\b\n" + p.read_text().replace("\n\n", "\n\n\b\n")


@click.group("lock", help=_lock_doc())
def lock_group() -> None:
    """Cross-instance mutual exclusion locks (e.g. e2e)."""


def _git_common_dir() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-common-dir"],
                       capture_output=True, text=True, check=False)
    if r.returncode != 0:
        click.echo(format_error("NotAGitRepo", r.stderr.strip() or "not a git repository", None), err=True)
        sys.exit(2)
    return Path(r.stdout.strip()).resolve()


def _lock_dir(name: str) -> Path:
    if not name.replace("-", "").replace("_", "").isalnum():
        click.echo(format_error("InvalidArgs", f"锁名仅允许字母数字/-/_: {name}", None), err=True)
        sys.exit(4)
    return _git_common_dir() / LOCKS_SUBDIR / f"{name}.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # 进程存在但属于其他用户
    return True


def _read_holder(lock_dir: Path) -> dict:
    holder_path = lock_dir / HOLDER_FILE
    if not holder_path.exists():
        return {}
    try:
        return yaml.safe_load(holder_path.read_text()) or {}
    except yaml.YAMLError:
        return {}


def _write_holder(lock_dir: Path, holder: str, pid: int) -> None:
    data = {
        "holder": holder,
        "pid": pid,
        "since": datetime.now().isoformat(timespec="seconds"),
    }
    (lock_dir / HOLDER_FILE).write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def _try_acquire(lock_dir: Path) -> bool:
    """mkdir 原子获取。True=拿到，False=已被占。"""
    try:
        os.mkdir(lock_dir)
        return True
    except FileExistsError:
        return False


@lock_group.command("acquire")
@click.argument("name")
@click.option("--holder", required=True, help="持有者标识（如 feature/002-xxx）")
@click.option("--pid", type=int, default=None,
              help="持有者进程 pid（用于 stale 检测；调用方传 $PPID 即实例 pid）")
@click.option("--force", is_flag=True, help="强制清锁后获取（人工确认对方已死后使用）")
def acquire(name: str, holder: str, pid: int | None, force: bool) -> None:
    """获取互斥锁。成功 exit 0；被活锁占用 exit 1（输出当前 holder 信息）."""
    lock_dir = _lock_dir(name)
    lock_dir.parent.mkdir(parents=True, exist_ok=True)

    if force and lock_dir.exists():
        old = _read_holder(lock_dir)
        shutil.rmtree(lock_dir)
        click.echo(f"Note: 强制清除旧锁 (holder={old.get('holder', '?')}, pid={old.get('pid', '?')})", err=True)

    if _try_acquire(lock_dir):
        _write_holder(lock_dir, holder, pid or 0)
        click.echo(f"Acquired {name} lock (holder={holder}, pid={pid or 0})")
        return

    # 锁被占：读 holder，做 stale 检测
    info = _read_holder(lock_dir)
    old_pid = int(info.get("pid") or 0)
    if not info:
        # 锁目录在但 holder 文件缺失/损坏 → 视为无效锁，清理重取
        shutil.rmtree(lock_dir)
        if _try_acquire(lock_dir):
            _write_holder(lock_dir, holder, pid or 0)
            click.echo(f"Acquired {name} lock (holder={holder}, pid={pid or 0}; 清理了无效旧锁)")
            return
    elif not _pid_alive(old_pid):
        # stale：holder 进程已死，清理重取
        shutil.rmtree(lock_dir)
        if _try_acquire(lock_dir):
            _write_holder(lock_dir, holder, pid or 0)
            click.echo(
                f"Acquired {name} lock (holder={holder}, pid={pid or 0}; "
                f"清理 stale 锁: 原 holder={info.get('holder', '?')}, pid={old_pid} 已死, since={info.get('since', '?')})")
            return

    # 活锁占用：输出 holder 信息，exit 1
    click.echo(format_error(
        "LockBusy",
        f"{name} lock 被占用: holder={info.get('holder', '?')}, pid={old_pid}, since={info.get('since', '?')}",
        "等对方释放；确认对方已死后用 acquire --force",
    ), err=True)
    sys.exit(1)


@lock_group.command("release")
@click.argument("name")
def release(name: str) -> None:
    """释放锁（幂等：无锁时输出提示，exit 0）."""
    lock_dir = _lock_dir(name)
    if not lock_dir.exists():
        click.echo(f"No {name} lock held")
        return
    info = _read_holder(lock_dir)
    shutil.rmtree(lock_dir)
    click.echo(f"Released {name} lock (holder={info.get('holder', '?')}, pid={info.get('pid', '?')})")


@lock_group.command("status")
@click.argument("name")
def status(name: str) -> None:
    """查看锁状态：free / held（含 holder 信息 + 存活检测）."""
    lock_dir = _lock_dir(name)
    if not lock_dir.exists():
        click.echo(f"{name}: free")
        return
    info = _read_holder(lock_dir)
    pid = int(info.get("pid") or 0)
    alive = "alive" if _pid_alive(pid) else "DEAD(stale)"
    click.echo(f"{name}: held")
    click.echo(f"  holder: {info.get('holder', '?')}")
    click.echo(f"  pid:    {pid} ({alive})")
    click.echo(f"  since:  {info.get('since', '?')}")
