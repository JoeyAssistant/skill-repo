"""CLI help 输出必须含关键信息（help 是命令文档唯一真值）.

防止 docstring 改动后 help 丢失关键字段说明。

注意：feature / issue 的 schema / state / workflow 唯一真源是 agent-pm.md
（PM system prompt），其 group help 只留指针；worktree / lock 的 help 仍是
doc/*.md 原文（命令签名与退出码，agent-pm.md 不重复维护）。
"""
from click.testing import CliRunner

from agent_factory.cli import main


def _help_output(*args) -> str:
    result = CliRunner().invoke(main, list(args) + ["--help"])
    assert result.exit_code == 0
    return result.output


def test_main_help_lists_groups():
    out = _help_output()
    assert "feature" in out
    assert "issue" in out
    assert "index" in out


def test_feature_help_points_to_single_source():
    """feature group help 指向 agent-pm.md（schema / state / workflow 的唯一真源）.

    doc/feature.md 不再重复维护这三项，只留指针 + CLI 侧约定。
    """
    out = _help_output("feature")
    assert "agent-pm.md" in out
    assert "唯一真源" in out
    # 命令清单由 click 自动生成（不来自 doc/feature.md），必须完整
    for cmd in ["new", "set", "show", "list", "transition", "delete"]:
        assert cmd in out, f"feature help missing command: {cmd}"


def test_issue_help_points_to_single_source():
    """issue group help 指向 agent-pm.md（唯一真源），命令清单完整."""
    out = _help_output("issue")
    assert "agent-pm.md" in out
    assert "唯一真源" in out
    for cmd in ["new", "set", "show", "list", "transition", "close"]:
        assert cmd in out, f"issue help missing command: {cmd}"


def test_worktree_help_shows_design_doc():
    """worktree group help 直接展示 doc/worktree.md 原文（目录约定 + 基线分支）."""
    out = _help_output("worktree")
    assert "feat-<NNN>-<slug>" in out
    assert "--base" in out
    assert "基线分支" in out


def test_index_help_contains_fields():
    out = _help_output("index")
    assert "priority" in out
    assert "status" in out
    assert "title" in out  # 不允许改 title 的说明


def test_issue_close_help_shows_both_paths():
    out = _help_output("issue", "close")
    assert "--bugfix" in out
    assert "--feature-request" in out
    assert "--fix-desc" in out
    assert "--verification" in out
    assert "--feature-id" in out
