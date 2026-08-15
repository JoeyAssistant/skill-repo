# agent_factory/schema/issue.py
"""Issue 模型（对应 .issues/<id>/ISSUE.yaml）."""
from __future__ import annotations
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class IssueStatus(str, Enum):
    """Issue 生命周期状态."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class BugfixResult(BaseModel):
    """bugfix 路径的处理结果."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["bugfix"] = "bugfix"
    fix_desc: str = Field(..., description="修改内容（developer 填）")
    verification: str = Field(..., description="PM 验收结果（基于 git show diff + 测试）")


class FeatureRequestResult(BaseModel):
    """feature_request 路径的处理结果."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["feature_request"] = "feature_request"
    feature_id: int = Field(..., description="转换到的 feature 编号")


# Discriminated union for result
IssueResult = Annotated[
    Union[BugfixResult, FeatureRequestResult],
    Field(discriminator="type"),
]


class Issue(BaseModel):
    """对应 .issues/<id>/ISSUE.yaml."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=999, description="issue 编号")
    title: str = Field(..., description="目录名（不可改，创建时通过 --slug 决定）")
    desc: str = Field(..., description="用户原始描述（create 时填，保留原话）")

    # PM 加工后填（信息收集阶段）
    scenario: Optional[str] = Field(None,
        description="问题场景：如何复现（PM 与用户讨论后填）")
    impact: Optional[str] = Field(None,
        description="问题影响：问题点 + 影响范围")

    # QA 诊断产出
    root_cause: Optional[str] = Field(None, description="根因")
    fix_plan: Optional[str] = Field(None,
        description="QA 给的方案（不预判 bugfix/feature，含问题分析 + 处理方向）")

    # 处理结果（in_progress → closed 时必填）
    result: Optional[IssueResult] = Field(None,
        description="issue 处理结果（bugfix 或 feature_request）")
