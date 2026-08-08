# agent-factory/schema/enums.py
"""agent-factory PM 工作流枚举定义."""
from enum import Enum


class AgentType(str, Enum):
    """Agent 形态."""
    CLI_ONLY = "cli-only"
    HTTP_API = "http-api"
    HTTP_WEB = "http-web"
    MCP_SERVER = "mcp-server"


class Priority(str, Enum):
    """优先级."""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class FeatureStatus(str, Enum):
    """Feature 生命周期状态."""
    DRAFT = "draft"
    DESIGNING = "designing"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    QA_REVIEWING = "qa-reviewing"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class IssueType(str, Enum):
    """Issue 类型."""
    BUG = "bug"
    FEATURE_REQUEST = "feature-request"


class IssueStatus(str, Enum):
    """Issue 生命周期状态."""
    OPEN = "open"
    TRIAGING = "triaging"
    CLOSED = "closed"


class DecisionStatus(str, Enum):
    """Decision（决策）状态."""
    OPEN = "open"
    CLOSED = "closed"
