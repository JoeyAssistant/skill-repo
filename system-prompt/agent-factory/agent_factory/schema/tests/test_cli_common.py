# agent_factory/schema/tests/test_cli_common.py
import pytest
from pathlib import Path
from agent_factory.cli.common import (
    load_yaml, dump_yaml, find_feature_dir, find_issue_dir,
    format_error, next_feature_id, next_issue_id
)
from agent_factory.schema import FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import FeatureStatus


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
    (tmp_path / ".features").mkdir()
    # Create directory with slug naming + index.yaml
    (tmp_path / ".features" / "001-test-feature").mkdir()
    (tmp_path / ".features" / "001-test-feature" / "REQUIREMENT.yaml").write_text("id: 1\n")
    dump_yaml(tmp_path / ".features" / "index.yaml", FeatureIndex(features=[
        FeatureIndexItem(id=1, title="001-test-feature", status=FeatureStatus.DRAFT, priority=Priority.P2),
    ]))
    p = find_feature_dir(1)
    assert p.exists()
    assert p.name == "001-test-feature"


def test_find_feature_dir_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    dump_yaml(tmp_path / ".features" / "index.yaml", FeatureIndex())
    with pytest.raises(FileNotFoundError, match="not in index"):
        find_feature_dir(999)


def test_find_feature_dir_no_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="Index file missing"):
        find_feature_dir(1)


def test_find_issue_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "001-test-issue").mkdir()
    (tmp_path / ".issues" / "001-test-issue" / "ISSUE.yaml").write_text("id: 1\n")
    from agent_factory.schema import IssueIndex, IssueIndexItem
    from agent_factory.schema.issue import IssueStatus
    dump_yaml(tmp_path / ".issues" / "index.yaml", IssueIndex(issues=[
        IssueIndexItem(id=1, title="001-test-issue", status=IssueStatus.OPEN, priority=Priority.P2),
    ]))
    p = find_issue_dir(1)
    assert p.exists()


def test_format_error():
    msg = format_error("ValidationError", "field X missing", ".features/1/REQUIREMENT.yaml")
    assert "ValidationError" in msg
    assert "field X missing" in msg
    assert ".features/1/REQUIREMENT.yaml" in msg


def test_next_feature_id_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    dump_yaml(tmp_path / ".features" / "index.yaml", {"features": []})
    assert next_feature_id() == 1


def test_next_feature_id_with_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    idx = FeatureIndex(features=[
        FeatureIndexItem(id=1, title="001-a", status=FeatureStatus.DRAFT, priority=Priority.P1),
        FeatureIndexItem(id=3, title="003-b", status=FeatureStatus.DONE, priority=Priority.P2),
    ])
    dump_yaml(tmp_path / ".features" / "index.yaml", idx.model_dump())
    assert next_feature_id() == 4


def test_next_issue_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    dump_yaml(tmp_path / ".issues" / "index.yaml", {"issues": []})
    assert next_issue_id() == 1
