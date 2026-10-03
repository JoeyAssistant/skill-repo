# agent-factory/schema/tests/test_enums.py
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import FeatureStatus
from agent_factory.schema.issue import IssueStatus


def test_priority_values():
    assert Priority.P1.value == "P1"
    assert Priority.P2.value == "P2"
    assert Priority.P3.value == "P3"


def test_feature_status_lifecycle():
    """FeatureStatus 覆盖完整生命周期"""
    expected = {"draft", "designing", "approved", "implementing",
                "qa-reviewing", "done", "cancelled"}
    actual = {s.value for s in FeatureStatus}
    assert actual == expected


def test_issue_status_lifecycle():
    expected = {"open", "in_progress", "closed"}
    actual = {s.value for s in IssueStatus}
    assert actual == expected


def test_enums_are_str_enums():
    """所有枚举应继承 str，便于 JSON 序列化"""
    for enum_cls in [Priority, FeatureStatus, IssueStatus]:
        assert issubclass(enum_cls, str)
