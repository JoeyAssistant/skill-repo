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


def test_issue_close_help_shows_reason_options():
    out = _help_output("issue", "close")
    assert "--reason-type" in out
    assert "--reason" in out
    assert "--bugfix" not in out


def test_issue_convert_help():
    out = _help_output("issue", "convert")
    assert "--slug" in out


def test_feature_help_shows_exit_codes():
    """feature group help 含退出码表（与 worktree / lock 对齐）."""
    out = _help_output("feature")
    assert "退出码" in out
    assert "0 成功 / 1 校验失败 / 2 资源不存在 / 3 状态机违规 / 4 参数错误" in out


def test_issue_help_shows_exit_codes():
    """issue group help 含退出码表."""
    out = _help_output("issue")
    assert "退出码" in out
    assert "0 成功 / 1 校验失败 / 2 资源不存在 / 3 状态机违规 / 4 参数错误" in out


def test_feature_set_help_shows_file_convention():
    """set help 含 --file 传值约定（多行长文本不用 inline）."""
    out = _help_output("feature", "set")
    assert "--file" in out
    assert "转义" in out


def test_issue_set_help_shows_file_convention():
    out = _help_output("issue", "set")
    assert "--file" in out
    assert "转义" in out


def test_missing_option_exits_4():
    """框架层参数解析错误（缺必填参数）映射为 exit 4「参数错误」.

    click UsageError 默认 exit 2，会与「资源不存在」撞车；CLI 在入口统一改映射。
    """
    result = CliRunner().invoke(main, ["feature", "new"])
    assert result.exit_code == 4
