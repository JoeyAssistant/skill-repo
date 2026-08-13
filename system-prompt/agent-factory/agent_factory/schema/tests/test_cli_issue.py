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


def test_issue_block_unblock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    # Block
    result = runner.invoke(main, ["issue", "block", "1", "--reason", "X", "--action", "Y"])
    assert result.exit_code == 0
    assert (tmp_path / ".issues" / "001-test-issue" / "BLOCKED.yaml").exists()

    # Unblock
    result = runner.invoke(main, ["issue", "unblock", "1", "--to", "in_progress"])
    assert result.exit_code == 0
    assert not (tmp_path / ".issues" / "001-test-issue" / "BLOCKED.yaml").exists()
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


def test_issue_close_bugfix(tmp_path, monkeypatch):
    """Close issue as bugfix via --bugfix flag."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    # Fill required fields
    runner.invoke(main, ["issue", "set", "1", "scenario", "复现"])
    runner.invoke(main, ["issue", "set", "1", "impact", "影响"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    runner.invoke(main, ["issue", "set", "1", "root_cause", "根因"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "方案"])

    # Close as bugfix
    result = runner.invoke(main, [
        "issue", "close", "1",
        "--bugfix",
        "--fix-desc", "改了 x.py",
        "--verification", "git show + test passed",
    ])
    assert result.exit_code == 0

    # Verify
    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["result"]["type"] == "bugfix"
    assert issue["result"]["fix_desc"] == "改了 x.py"
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "closed"


def test_issue_close_feature_request(tmp_path, monkeypatch):
    """Close issue as feature_request via --feature-request flag."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "x"])
    runner.invoke(main, ["issue", "set", "1", "impact", "y"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    runner.invoke(main, ["issue", "set", "1", "root_cause", "x"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "y"])

    result = runner.invoke(main, [
        "issue", "close", "1",
        "--feature-request",
        "--feature-id", "70",
    ])
    assert result.exit_code == 0

    issue = load_yaml(tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml")
    assert issue["result"]["type"] == "feature_request"
    assert issue["result"]["feature_id"] == 70


def test_issue_close_requires_exactly_one_path(tmp_path, monkeypatch):
    """--bugfix and --feature-request are mutually exclusive."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "close", "1",
        "--bugfix", "--feature-request",
    ])
    assert result.exit_code == 4  # invalid args


def test_issue_close_neither_flag(tmp_path, monkeypatch):
    """Must specify either --bugfix or --feature-request."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "close", "1",
    ])
    assert result.exit_code == 4  # invalid args


def test_issue_close_bugfix_requires_fix_desc_and_verification(tmp_path, monkeypatch):
    """--bugfix requires both --fix-desc and --verification."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "close", "1",
        "--bugfix",
        "--fix-desc", "改了",
    ])
    assert result.exit_code == 4  # missing --verification


def test_issue_show_with_result(tmp_path, monkeypatch):
    """show renders result fields."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["issue", "set", "1", "scenario", "x"])
    runner.invoke(main, ["issue", "set", "1", "impact", "y"])
    runner.invoke(main, ["issue", "transition", "1", "--to", "in_progress"])
    runner.invoke(main, ["issue", "set", "1", "root_cause", "x"])
    runner.invoke(main, ["issue", "set", "1", "fix_plan", "y"])
    runner.invoke(main, [
        "issue", "close", "1",
        "--bugfix",
        "--fix-desc", "改了 x.py",
        "--verification", "通过",
    ])

    result = runner.invoke(main, ["issue", "show", "1"])
    assert result.exit_code == 0
    assert "bugfix" in result.output
    assert "改了 x.py" in result.output
