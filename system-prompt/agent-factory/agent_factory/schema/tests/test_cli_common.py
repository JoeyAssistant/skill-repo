# agent_factory/schema/tests/test_cli_common.py
import pytest
from pathlib import Path
from agent_factory.cli.common import (
    load_yaml, dump_yaml, find_feature_dir, find_issue_dir,
    format_error, next_feature_id, next_issue_id
)
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import FeatureStatus, Priority


def test_load_yaml(tmp_path):
    f = tmp_path / "test.yaml"
    f.write_text("id: 1\nname: test\n")
    data = load_yaml(f)
    assert data == {"id": 1, "name": "test"}


def test_dump_yaml(tmp_path):
    f = tmp_path / "out.yaml"
    dump_yaml(f, {"id": 1, "name": "测试"})
    content = f.read_text()
    assert "id: 1" in content
    assert "name: 测试" in content  # Unicode preserved


def test_find_feature_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text("id: 1\n")
    p = find_feature_dir(1)
    assert p.exists()
    assert p.name == "1"


def test_find_feature_dir_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        find_feature_dir(999)


def test_find_issue_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues" / "1").mkdir(parents=True)
    (tmp_path / ".issues" / "1" / "ISSUE.yaml").write_text("id: 1\n")
    p = find_issue_dir(1)
    assert p.exists()


def test_format_error():
    msg = format_error("ValidationError", "field X missing", ".features/1/REQUIREMENTS.yaml")
    assert "ValidationError" in msg
    assert "field X missing" in msg
    assert ".features/1/REQUIREMENTS.yaml" in msg


def test_next_feature_id_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    dump_yaml(tmp_path / ".features" / "index.yaml", {"features": []})
    assert next_feature_id() == 1


def test_next_feature_id_with_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    idx = FeatureIndex(features=[
        FeatureIndexItem(id=1, title="A", status=FeatureStatus.DRAFT, priority=Priority.P1),
        FeatureIndexItem(id=3, title="B", status=FeatureStatus.DONE, priority=Priority.P2),
    ])
    dump_yaml(tmp_path / ".features" / "index.yaml", idx.model_dump())
    assert next_feature_id() == 4


def test_next_issue_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    dump_yaml(tmp_path / ".issues" / "index.yaml", {"issues": []})
    assert next_issue_id() == 1
