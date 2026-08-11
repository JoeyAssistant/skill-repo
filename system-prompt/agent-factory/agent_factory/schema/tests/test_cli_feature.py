# agent_factory/schema/tests/test_cli_feature.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def test_feature_new_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Initialize empty index
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "收入管理",
        "--slug", "income-module",
        "--agent-type", "cli-only",
        "--priority", "P1",
    ])
    assert result.exit_code == 0, result.output
    assert "Created feature 1" in result.output
    assert "001-income-module" in result.output

    # REQS.yaml created with slug-named directory
    reqs = tmp_path / ".features" / "001-income-module" / "REQUIREMENTS.yaml"
    assert reqs.exists()
    data = load_yaml(reqs)
    assert data["id"] == 1
    assert data["title"] == "001-income-module"
    assert data["agent_type"] == "cli-only"

    # Index updated
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 1
    assert idx["features"][0]["id"] == 1
    assert idx["features"][0]["title"] == "001-income-module"
    assert idx["features"][0]["status"] == "draft"
    assert idx["features"][0]["priority"] == "P1"


def test_feature_new_invalid_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "X",
        "--slug", "Invalid_Slug",
    ])
    assert result.exit_code == 4  # InvalidSlug


def test_feature_new_slug_must_start_with_letter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "X",
        "--slug", "123-abc",
    ])
    assert result.exit_code == 4


def test_feature_new_default_agent_type_and_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "X", "--slug", "x"])
    assert result.exit_code == 0

    reqs = load_yaml(tmp_path / ".features" / "001-x" / "REQUIREMENTS.yaml")
    assert reqs["agent_type"] == "cli-only"  # default
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P2"  # default


def test_feature_new_invalid_agent_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new", "--title", "X", "--slug", "x", "--agent-type", "unknown-type",
    ])
    assert result.exit_code != 0  # click rejects invalid choice


def test_feature_new_increments_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "B", "--slug", "b"])
    assert result.exit_code == 0
    assert "Created feature 2" in result.output
    assert "002-b" in result.output


def test_feature_set_simple_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "problem", "新问题描述",
    ])
    assert result.exit_code == 0, result.output
    assert "Updated feature 1: problem" in result.output

    reqs = load_yaml(tmp_path / ".features" / "001-test-feature" / "REQUIREMENTS.yaml")
    assert reqs["problem"] == "新问题描述"


def test_feature_set_long_field_from_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    # Write long content to temp file
    long_content = "这是详细描述\n含多行\n第三行"
    desc_file = tmp_path / "desc.md"
    desc_file.write_text(long_content)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "description", "--file", str(desc_file),
    ])
    assert result.exit_code == 0, result.output

    reqs = load_yaml(tmp_path / ".features" / "001-test-feature" / "REQUIREMENTS.yaml")
    assert reqs["description"] == long_content


def test_feature_set_title_rejected(tmp_path, monkeypatch):
    """title is immutable (equals directory name)."""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "title", "新标题",
    ])
    assert result.exit_code != 0  # title not in REQS_FIELDS


def test_feature_set_invalid_field_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "nonexistent_field", "value",
    ])
    assert result.exit_code != 0


def test_feature_set_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "999", "problem", "X",
    ])
    assert result.exit_code == 2


def _setup_feature(tmp_path):
    """Helper: create .features/001-test-feature/REQUIREMENTS.yaml + index.yaml entry."""
    (tmp_path / ".features" / "001-test-feature").mkdir(parents=True)
    (tmp_path / ".features" / "001-test-feature" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: '001-test-feature'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-test-feature'\n    status: draft\n    priority: P2\n"
    )


def test_feature_show_markdown_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0
    assert "001-test-feature" in result.output  # title rendered


def test_feature_show_yaml_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "yaml"])
    assert result.exit_code == 0
    assert "id: 1" in result.output
    assert "001-test-feature" in result.output


def test_feature_show_json_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["id"] == 1
    assert data["title"] == "001-test-feature"


def test_feature_show_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "999"])
    assert result.exit_code == 2


def test_feature_list_default_table(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list"])
    assert result.exit_code == 0
    assert "1" in result.output
    assert "001-test-feature" in result.output


def test_feature_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Setup 2 features: one draft, one done
    (tmp_path / ".features" / "001-a").mkdir(parents=True)
    (tmp_path / ".features" / "001-a" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: '001-a'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "002-b").mkdir(parents=True)
    (tmp_path / ".features" / "002-b" / "REQUIREMENTS.yaml").write_text(
        "id: 2\ntitle: '002-b'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n"
        "  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
        "  - id: 2\n    title: '002-b'\n    status: done\n    priority: P1\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list", "--status", "done"])
    assert result.exit_code == 0
    assert "002-b" in result.output
    assert "001-a\n" not in result.output  # filtered out (full line)


def test_feature_transition_draft_to_designing_requires_description(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)  # description is "z" (non-empty)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 0
    assert "draft → designing" in result.output

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "designing"


def test_feature_transition_blocked_when_description_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # Set description to empty
    (tmp_path / ".features" / "001-test-feature" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: '001-test-feature'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: ''\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 1  # validation failure
    # Status unchanged
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "draft"


def test_feature_transition_designing_to_approved_requires_all_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # First transition to designing
    runner = CliRunner()
    runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])

    # Try transition to approved without data_schema etc.
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 1  # missing data_schema / interfaces / acceptance_cases


def test_feature_transition_invalid_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    # draft → done is invalid (must go through designing, approved, implementing, qa-reviewing)
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "done"])
    assert result.exit_code == 3  # invalid state path


def test_feature_block_creates_blocked_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "block", "1",
        "--reason", "卡住了",
        "--action", "等用户决策",
    ])
    assert result.exit_code == 0
    assert "Blocked feature 1" in result.output

    blocked = tmp_path / ".features" / "001-test-feature" / "BLOCKED.yaml"
    assert blocked.exists()
    data = load_yaml(blocked)
    assert data["reason"] == "卡住了"
    assert data["action"] == "等用户决策"

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "blocked"


def test_feature_block_already_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    runner.invoke(main, ["feature", "block", "1", "--reason", "X", "--action", "Y"])
    result = runner.invoke(main, ["feature", "block", "1", "--reason", "X2", "--action", "Y2"])
    assert result.exit_code == 1  # already blocked


def test_feature_unblock_removes_blocked_yaml_and_restores_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # Block first
    runner = CliRunner()
    runner.invoke(main, ["feature", "block", "1", "--reason", "X", "--action", "Y"])

    # Now unblock to designing
    result = runner.invoke(main, ["feature", "unblock", "1", "--to", "designing"])
    assert result.exit_code == 0
    assert "Unblocked feature 1" in result.output

    assert not (tmp_path / ".features" / "001-test-feature" / "BLOCKED.yaml").exists()
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "designing"


def test_feature_unblock_not_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "unblock", "1", "--to", "designing"])
    assert result.exit_code == 1  # not blocked


def test_feature_delete_requires_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "1"])
    assert result.exit_code == 1  # --force required


def test_feature_delete_with_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "1", "--force"])
    assert result.exit_code == 0
    assert "Deleted feature 1" in result.output

    assert not (tmp_path / ".features" / "001-test-feature").exists()
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 0


def test_feature_delete_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "999", "--force"])
    assert result.exit_code == 2
