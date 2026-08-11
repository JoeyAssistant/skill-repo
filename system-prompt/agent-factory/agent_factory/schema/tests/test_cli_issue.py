# agent_factory/schema/tests/test_cli_issue.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def _setup_issue(tmp_path):
    """Helper: create .issues/001-test-issue/ISSUE.yaml + index.yaml entry."""
    (tmp_path / ".issues" / "001-test-issue").mkdir(parents=True)
    (tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: '001-test-issue'\nscenario: 复现步骤\nimpact: 影响范围\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: '001-test-issue'\n    type: bug\n    status: open\n    priority: P2\n"
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
        "--type", "bug",
        "--priority", "P1",
    ])
    assert result.exit_code == 0
    assert "Created issue 1" in result.output
    assert "001-login-crash" in result.output

    issue = load_yaml(tmp_path / ".issues" / "001-login-crash" / "ISSUE.yaml")
    assert issue["title"] == "001-login-crash"

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["type"] == "bug"
    assert idx["issues"][0]["priority"] == "P1"


def test_issue_new_invalid_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "new",
        "--title", "X",
        "--slug", "INVALID",
        "--type", "bug",
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


def test_issue_list_filter_by_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "list", "--type", "bug"])
    assert result.exit_code == 0
    assert "001-test-issue" in result.output


def test_issue_transition_open_to_triaging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "transition", "1", "--to", "triaging"])
    assert result.exit_code == 0
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "triaging"


def test_issue_block_unblock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    # Block
    result = runner.invoke(main, ["issue", "block", "1", "--reason", "X", "--action", "Y"])
    assert result.exit_code == 0
    assert (tmp_path / ".issues" / "001-test-issue" / "BLOCKED.yaml").exists()

    # Unblock
    result = runner.invoke(main, ["issue", "unblock", "1", "--to", "triaging"])
    assert result.exit_code == 0
    assert not (tmp_path / ".issues" / "001-test-issue" / "BLOCKED.yaml").exists()
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "triaging"


def test_issue_close_requires_fix_and_resolution(tmp_path, monkeypatch):
    """triaging → closed must have fix + resolution both non-empty (闭环校验)."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    # First transition to triaging
    runner.invoke(main, ["issue", "transition", "1", "--to", "triaging"])

    # Try to close without fix + resolution → should fail
    result = runner.invoke(main, ["issue", "transition", "1", "--to", "closed"])
    assert result.exit_code == 1  # validation failure
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "triaging"  # unchanged


def test_issue_close_with_fix_only_still_fails(tmp_path, monkeypatch):
    """fix filled but resolution empty → still cannot close."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    runner.invoke(main, ["issue", "transition", "1", "--to", "triaging"])
    runner.invoke(main, ["issue", "set", "1", "fix", "Changed Files: x.py"])

    result = runner.invoke(main, ["issue", "transition", "1", "--to", "closed"])
    assert result.exit_code == 1  # resolution still empty


def test_issue_close_succeeds_with_both_fields(tmp_path, monkeypatch):
    """Both fix and resolution filled → close succeeds."""
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    runner.invoke(main, ["issue", "transition", "1", "--to", "triaging"])
    runner.invoke(main, ["issue", "set", "1", "fix", "Changed Files: x.py"])
    runner.invoke(main, ["issue", "set", "1", "resolution", "direct-fix"])

    result = runner.invoke(main, ["issue", "transition", "1", "--to", "closed"])
    assert result.exit_code == 0
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "closed"
