# agent_factory/schema/tests/test_cli_index.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def test_index_set_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
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
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "status", "done"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "done"


def test_index_set_title_rejected(tmp_path, monkeypatch):
    """title must be set via feature/issue set, not index set."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "title", "新"])
    assert result.exit_code != 0  # rejected


def test_index_set_issue_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: A\n    type: bug\n    status: open\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "issue", "1", "type", "feature-request"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["type"] == "feature-request"


def test_index_refresh_rebuilds_feature_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create 2 features without proper index
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: A\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "2").mkdir(parents=True)
    (tmp_path / ".features" / "2" / "REQUIREMENTS.yaml").write_text(
        "id: 2\ntitle: B\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    # Empty / corrupt index
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "feature"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 2
    titles = [f["title"] for f in idx["features"]]
    assert "A" in titles
    assert "B" in titles


def test_index_refresh_issue_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues" / "1").mkdir(parents=True)
    (tmp_path / ".issues" / "1" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: A\nscenario: x\nimpact: y\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "issue"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert len(idx["issues"]) == 1
