# agent-factory/schema/tests/test_enums.py
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import AgentType, DecisionStatus, FeatureStatus
from agent_factory.schema.issue import IssueStatus


def test_agent_type_values():
    assert AgentType.CLI_ONLY.value == "cli-only"
    assert AgentType.HTTP_API.value == "http-api"
    assert AgentType.HTTP_WEB.value == "http-web"
    assert AgentType.MCP_SERVER.value == "mcp-server"
    assert len(list(AgentType)) == 4


def test_priority_values():
    assert Priority.P1.value == "P1"
    assert Priority.P2.value == "P2"
    assert Priority.P3.value == "P3"


def test_feature_status_lifecycle():
    """FeatureStatus 覆盖完整生命周期"""
    expected = {"draft", "designing", "approved", "implementing",
                "qa-reviewing", "done", "blocked", "cancelled"}
    actual = {s.value for s in FeatureStatus}
    assert actual == expected


def test_issue_status_lifecycle():
    expected = {"open", "in_progress", "closed"}
    actual = {s.value for s in IssueStatus}
    assert actual == expected


def test_decision_status_values():
    assert DecisionStatus.OPEN.value == "open"
    assert DecisionStatus.CLOSED.value == "closed"


def test_enums_are_str_enums():
    """所有枚举应继承 str，便于 JSON 序列化"""
    for enum_cls in [AgentType, Priority, FeatureStatus,
                     IssueStatus, DecisionStatus]:
        assert issubclass(enum_cls, str)
