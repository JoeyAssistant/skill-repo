# agent_factory/schema/tests/test_cli_issue.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def _setup_issue(tmp_path):
    """Helper: create .issues/001-test-issue/ISSUE.yaml + index.yaml entry."""
    (tmp_path / ".issues" / "001-test-issue").mkdir(parents=True)
    (tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: '001-test-issue'\ndesc: '用户原始描述'\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: '001-test-issue'\n    status: open\n    priority: P2\n"
    )


def test_issue_new_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "new",
        "--title", "登录崩溃",
        "--slug", "login-crash",
        "--desc", "用户反馈登录就崩溃了",
        "--priority", "P1",
    ])
    assert result.exit_code == 0
    assert "Created issue 1" in result.output
    assert "001-login-crash" in result.output

    issue = load_yaml(tmp_path / ".issues" / "001-login-crash" / "ISSUE.yaml")
    assert issue["title"] == "001-login-crash"
    assert issue["desc"] == "用户反馈登录就崩溃了"

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["priority"] == "P1"


def test_issue_new_requires_desc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "new", "--title", "X", "--slug", "test"])
    assert result.exit_code != 0  # --desc required


def test_issue_new_invalid_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "new",
        "--title", "X",
        "--slug", "INVALID",
        "--desc", "test",
    ])
    assert result.exit_code == 4  # InvalidSlug


def test_issue_set_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "set", "1", "root_cause", "代码 bug",
    ])
    assert result.exit_code == 0

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["root_cause"] == "代码 bug"


def test_issue_set_desc(tmp_path, monkeypatch):
    """desc field can be set after creation."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "set", "1", "desc", "新的描述",
    ])
    assert result.exit_code == 0

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["desc"] == "新的描述"


def test_issue_new_with_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "new",
        "--title", "登录崩溃",
        "--slug", "login-crash",
        "--desc", "用户原话",
        "--summary", "登录点击提交白屏，所有用户无法登录",
    ])
    assert result.exit_code == 0, result.output

    data = load_yaml(tmp_path / ".issues" / "001-login-crash" / "ISSUE.yaml")
    assert data["summary"] == "登录点击提交白屏，所有用户无法登录"


def test_issue_set_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "set", "1", "summary", "登录点击提交白屏，所有用户无法登录",
    ])
    assert result.exit_code == 0, result.output

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["summary"] == "登录点击提交白屏，所有用户无法登录"


def test_issue_set_summary_too_long_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "set", "1", "summary", "一" * 51])
    assert result.exit_code == 1  # ValidationError


def test_issue_show_renders_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    p = tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml"
    p.write_text(p.read_text() + "summary: 登录点击提交白屏，所有用户无法登录\n")

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "show", "1"])
    assert result.exit_code == 0, result.output
    assert "登录点击提交白屏，所有用户无法登录" in result.output


def test_issue_list_table_includes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    p = tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml"
    p.write_text(p.read_text() + "summary: 登录点击提交白屏\n")

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "list"])
    assert result.exit_code == 0, result.output
    assert "登录点击提交白屏" in result.output


def test_issue_list_json_includes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    p = tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml"
    p.write_text(p.read_text() + "summary: 登录点击提交白屏\n")

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "list", "--format", "json"])
    assert result.exit_code == 0, result.output
    import json
    rows = json.loads(result.output)
    assert rows[0]["summary"] == "登录点击提交白屏"


def test_issue_set_title_rejected(tmp_path, monkeypatch):
    """title is immutable (equals directory name)."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "set", "1", "title", "新标题",
    ])
    assert result.exit_code != 0  # title not in ISSUE_FIELDS


def test_issue_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "show", "1"])
    assert result.exit_code == 0
    assert "001-test-issue" in result.output
    assert "Description" in result.output


def test_issue_list_no_type_filter(tmp_path, monkeypatch):
    """issue list no longer has --type filter."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "list"])
    assert result.exit_code == 0
    assert "001-test-issue" in result.output


def test_issue_open_to_in_progress_requires_scenario_impact(tmp_path, monkeypatch):
    """open → in_progress must have scenario + impact filled."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)  # only has id/title/desc

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    assert result.exit_code == 1  # validation failure
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "open"  # unchanged


def test_issue_open_to_in_progress_succeeds_when_fields_filled(tmp_path, monkeypatch):
    """open → in_progress succeeds when scenario + impact both filled."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "复现步骤"])
    runner.invoke(main, ["issue", "set", "1", "impact", "影响范围"])

    result = runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    assert result.exit_code == 0
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "in_progress"


def test_issue_close_requires_result(tmp_path, monkeypatch):
    """in_progress → closed requires result (via issue close command)."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    # Fill scenario/impact and transition to in_progress
    runner.invoke(main, ["issue", "set", "1", "scenario", "x"])
    runner.invoke(main, ["issue", "set", "1", "impact", "y"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])

    # Fill QA fields
    runner.invoke(main, ["issue", "set", "1", "root_cause", "x"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "y"])

    # Try to close without result → should fail
    result = runner.invoke(main, ["issue", "transition", "1", "--to", "closed"])
    assert result.exit_code == 1  # result is empty
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "in_progress"  # unchanged


def test_issue_close_with_reason(tmp_path, monkeypatch):
    """Close issue without feature via --reason-type + --reason."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "close", "1",
        "--reason-type", "wontfix",
        "--reason", "暂不处理",
    ])
    assert result.exit_code == 0

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["result"]["type"] == "closed"
    assert issue["result"]["reason_type"] == "wontfix"
    assert issue["result"]["reason"] == "暂不处理"
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "closed"


def test_issue_close_requires_reason(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["issue", "close", "1", "--reason-type", "invalid"])
    assert result.exit_code != 0  # --reason required


def test_issue_convert_creates_feature_and_closes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "复现步骤"])
    runner.invoke(main, ["issue", "set", "1", "impact", "影响范围"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    runner.invoke(main, ["issue", "set", "1", "root_cause", "根因"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "修复方向"])

    result = runner.invoke(main, ["issue", "convert", "1", "--slug", "login-crash"])
    assert result.exit_code == 0
    assert "Converted issue 1 to feature 1" in result.output

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["result"]["type"] == "converted_to_feature"
    assert issue["result"]["feature_id"] == 1

    feature = load_yaml(tmp_path / ".features" / "001-login-crash" / "FEATURE.yaml")
    assert feature["id"] == 1
    assert feature["desc"] == "用户原始描述"
    assert feature["source_issue"] == 1
    assert feature.get("background") is None  # pain_point 由 PM 重新提炼写入，不从 impact 搬运

    feat_idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert feat_idx["features"][0]["status"] == "draft"

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "closed"


def test_issue_convert_requires_in_progress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["issue", "convert", "1", "--slug", "login-crash"])
    assert result.exit_code == 3  # invalid transition
    assert not (tmp_path / ".features" / "001-login-crash").exists()


def test_issue_convert_requires_analysis(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "x"])
    runner.invoke(main, ["issue", "set", "1", "impact", "y"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])

    result = runner.invoke(main, ["issue", "convert", "1", "--slug", "login-crash"])
    assert result.exit_code == 1  # root_cause/fix_plan missing
    assert not (tmp_path / ".features" / "001-login-crash").exists()


def test_issue_show_with_converted_result(tmp_path, monkeypatch):
    """show renders converted result and linked feature status."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "x"])
    runner.invoke(main, ["issue", "set", "1", "impact", "y"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    runner.invoke(main, ["issue", "set", "1", "root_cause", "x"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "y"])
    runner.invoke(main, ["issue", "convert", "1", "--slug", "login-crash"])

    result = runner.invoke(main, ["issue", "show", "1"])
    assert result.exit_code == 0
    assert "converted_to_feature" in result.output
    assert "feature_id" in result.output
    assert "feature_status" in result.output
    assert "draft" in result.output
