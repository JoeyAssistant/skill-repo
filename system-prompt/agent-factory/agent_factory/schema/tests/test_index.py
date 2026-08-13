# agent_factory/schema/tests/test_index.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.enums import (
    FeatureStatus, IssueStatus, Priority,
)
from agent_factory.schema.index import (
    FeatureIndex, FeatureIndexItem,
    IssueIndex, IssueIndexItem,
)


# === FeatureIndex 测试 ===

def test_feature_index_item_valid():
    item = FeatureIndexItem(
        id=1,
        title="收入管理模块",
        status=FeatureStatus.DONE,
        priority=Priority.P1,
    )
    assert item.id == 1
    assert item.status == FeatureStatus.DONE


def test_feature_index_item_extra_field_forbidden():
    with pytest.raises(ValidationError):
        FeatureIndexItem(
            id=1, title="...", status=FeatureStatus.DRAFT,
            priority=Priority.P1, extra="x",
        )


def test_feature_index_empty():
    idx = FeatureIndex()
    assert idx.features == []


def test_feature_index_with_items():
    idx = FeatureIndex(features=[
        FeatureIndexItem(id=1, title="A", status=FeatureStatus.DRAFT, priority=Priority.P1),
        FeatureIndexItem(id=2, title="B", status=FeatureStatus.DONE, priority=Priority.P2),
    ])
    assert len(idx.features) == 2
    assert idx.features[1].id == 2


# === IssueIndex 测试 ===

def test_issue_index_item_valid():
    item = IssueIndexItem(
        id=1,
        title="登录崩溃",
        status=IssueStatus.CLOSED,
        priority=Priority.P1,
    )
    assert item.status == IssueStatus.CLOSED


def test_issue_index_item_extra_field_forbidden():
    with pytest.raises(ValidationError):
        IssueIndexItem(
            id=1, title="...",
            status=IssueStatus.OPEN, priority=Priority.P1, extra="x",
        )


def test_issue_index_with_items():
    idx = IssueIndex(issues=[
        IssueIndexItem(id=1, title="A",
                       status=IssueStatus.CLOSED, priority=Priority.P1),
        IssueIndexItem(id=2, title="B",
                       status=IssueStatus.OPEN, priority=Priority.P2),
    ])
    assert len(idx.issues) == 2
    assert idx.issues[1].status == IssueStatus.OPEN
