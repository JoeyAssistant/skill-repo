# agent_factory/schema/index.py
"""Index 模型（对应 .features/index.yaml 和 .issues/index.yaml）."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import FeatureStatus
from agent_factory.schema.issue import IssueStatus


class FeatureIndexItem(BaseModel):
    """feature index 单行."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="feature 编号")
    title: str = Field(..., description="人读展示标题")
    status: FeatureStatus = Field(..., description="调度核心：当前生命周期状态")
    priority: Priority = Field(..., description="调度排序：优先级")


class FeatureIndex(BaseModel):
    """对应 .features/index.yaml."""
    model_config = ConfigDict(extra="forbid")

    features: list[FeatureIndexItem] = Field(default_factory=list,
        description="所有 feature 的索引行")


class IssueIndexItem(BaseModel):
    """issue index 单行（4 字段，与 FeatureIndexItem 一致）."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="issue 编号")
    title: str = Field(..., description="人读展示标题")
    status: IssueStatus = Field(..., description="调度核心：当前生命周期状态")
    priority: Priority = Field(..., description="调度排序：优先级")


class IssueIndex(BaseModel):
    """对应 .issues/index.yaml."""
    model_config = ConfigDict(extra="forbid")

    issues: list[IssueIndexItem] = Field(default_factory=list,
        description="所有 issue 的索引行")
