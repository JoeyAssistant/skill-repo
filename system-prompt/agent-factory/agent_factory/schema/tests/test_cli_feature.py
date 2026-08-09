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
        "--agent-type", "cli-only",
        "--priority", "P1",
    ])
    assert result.exit_code == 0, result.output
    assert "Created feature 1" in result.output

    # REQS.yaml created
    reqs = tmp_path / ".features" / "1" / "REQUIREMENTS.yaml"
    assert reqs.exists()
    data = load_yaml(reqs)
    assert data["id"] == 1
    assert data["title"] == "收入管理"
    assert data["agent_type"] == "cli-only"

    # Index updated
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 1
    assert idx["features"][0]["id"] == 1
    assert idx["features"][0]["title"] == "收入管理"
    assert idx["features"][0]["status"] == "draft"
    assert idx["features"][0]["priority"] == "P1"


def test_feature_new_default_agent_type_and_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "X"])
    assert result.exit_code == 0

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["agent_type"] == "cli-only"  # default
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P2"  # default


def test_feature_new_invalid_agent_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new", "--title", "X", "--agent-type", "unknown-type",
    ])
    assert result.exit_code != 0  # click rejects invalid choice


def test_feature_new_increments_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "B"])
    assert result.exit_code == 0
    assert "Created feature 2" in result.output
