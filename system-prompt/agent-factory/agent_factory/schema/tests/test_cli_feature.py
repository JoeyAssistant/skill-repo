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


def test_feature_set_simple_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "problem", "新问题描述",
    ])
    assert result.exit_code == 0, result.output
    assert "Updated feature 1: problem" in result.output

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
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

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["description"] == long_content


def test_feature_set_title_syncs_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "title", "新标题",
    ])
    assert result.exit_code == 0

    # REQS updated
    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["title"] == "新标题"
    # Index also updated (sync)
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["title"] == "新标题"


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
    """Helper: create .features/1/REQUIREMENTS.yaml + index.yaml entry."""
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: 测试\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: 测试\n    status: draft\n    priority: P2\n"
    )
