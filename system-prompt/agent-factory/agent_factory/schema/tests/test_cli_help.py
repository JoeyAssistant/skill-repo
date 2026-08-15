"""CLI help 输出必须含关键信息（help 是命令文档唯一真值）.

防止 docstring 改动后 help 丢失关键字段说明。
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


def test_feature_help_contains_fields_and_state_machine():
    out = _help_output("feature")
    # 支持字段
    for field in ["agent_type", "problem", "benefit", "description",
                  "data_schema", "interfaces", "acceptance_cases", "decisions"]:
        assert field in out, f"feature help missing field: {field}"
    # 状态机
    assert "designing" in out
    assert "approved" in out


def test_issue_help_shows_design_doc():
    """issue group help 直接展示 doc/issue.md 原文（schema 字段 + workflow）."""
    out = _help_output("issue")
    # schema 字段（issue.md 原文）
    for field in ["desc", "scenario", "impact", "root_cause", "fix_plan", "result"]:
        assert field in out, f"issue help missing field: {field}"
    # workflow 关键节点（issue.md 原文 mermaid）
    assert "提一个issue" in out
    assert "root_cause + fix_plan" in out
    assert "bugfix" in out
    assert "feature_id" in out


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
