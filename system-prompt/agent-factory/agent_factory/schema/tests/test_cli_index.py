# agent_factory/schema/tests/test_cli_index.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def test_index_set_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "priority", "P1"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P1"


def test_index_set_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "status", "done"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "done"


def test_index_set_title_rejected(tmp_path, monkeypatch):
    """title must be set via feature/issue new --slug, not index set."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "title", "新"])
    assert result.exit_code != 0  # rejected


def test_index_set_issue_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: '001-a'\n    type: bug\n    status: open\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "issue", "1", "type", "feature-request"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["type"] == "feature-request"


def test_index_refresh_rebuilds_feature_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create 2 features with slug naming
    (tmp_path / ".features" / "001-alpha").mkdir(parents=True)
    (tmp_path / ".features" / "001-alpha" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: '001-alpha'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "002-beta").mkdir(parents=True)
    (tmp_path / ".features" / "002-beta" / "REQUIREMENTS.yaml").write_text(
        "id: 2\ntitle: '002-beta'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    # Empty / corrupt index
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "feature"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 2
    titles = [f["title"] for f in idx["features"]]
    assert "001-alpha" in titles
    assert "002-beta" in titles


def test_index_refresh_issue_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues" / "001-bug-one").mkdir(parents=True)
    (tmp_path / ".issues" / "001-bug-one" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: '001-bug-one'\nscenario: x\nimpact: y\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "issue"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert len(idx["issues"]) == 1
    assert idx["issues"][0]["title"] == "001-bug-one"


def test_index_refresh_uses_directory_name_as_title(tmp_path, monkeypatch):
    """refresh uses directory name (not YAML content) as title."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features" / "057-cli-only-data-access").mkdir(parents=True)
    (tmp_path / ".features" / "057-cli-only-data-access" / "REQUIREMENTS.yaml").write_text(
        "id: 57\ntitle: '001-alpha'\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "feature"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["title"] == "057-cli-only-data-access"
    assert idx["features"][0]["id"] == 57
