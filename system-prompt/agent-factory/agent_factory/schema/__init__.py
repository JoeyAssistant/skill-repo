# agent_factory/schema/__init__.py
"""agent-factory PM 工作流 schema.

提供 5 个核心模型：
- Feature：feature 需求规格
- Issue：issue 报告
- FeatureIndex / FeatureIndexItem：feature 索引
- IssueIndex / IssueIndexItem：issue 索引
- BlockedRecord：阻塞记录
"""
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import AgentType, FeatureStatus
from agent_factory.schema.issue import IssueStatus
from agent_factory.schema.feature import Background, Feature, ModuleSpec, FeatureTestCase
from agent_factory.schema.issue import (
    BugfixResult,
    FeatureRequestResult,
    Issue,
    IssueResult,
)
from agent_factory.schema.index import (
    FeatureIndex,
    FeatureIndexItem,
    IssueIndex,
    IssueIndexItem,
)
from agent_factory.schema.blocked import BlockedRecord

__all__ = [
    # 枚举
    "AgentType",
    "FeatureStatus",
    "IssueStatus",
    "Priority",
    # Feature 系列
    "Feature",
    "Background",
    "ModuleSpec",
    "FeatureTestCase",
    # Issue
    "Issue",
    "BugfixResult",
    "FeatureRequestResult",
    "IssueResult",
    # Index 系列
    "FeatureIndex",
    "FeatureIndexItem",
    "IssueIndex",
    "IssueIndexItem",
    # Blocked
    "BlockedRecord",
]
