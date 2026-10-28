# agent_factory/schema/issue.py
"""Issue 模型（对应 .issues/<id>/ISSUE.yaml）."""
from __future__ import annotations
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_factory.schema.compat import migrate_legacy_desc


class IssueStatus(str, Enum):
    """Issue 生命周期状态."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class IssueCloseReason(str, Enum):
    """issue 无 feature 关闭的原因分类."""
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    WONTFIX = "wontfix"
    NO_ACTION = "no_action"


class ConvertedResult(BaseModel):
    """转 feature 的处理结果."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["converted_to_feature"] = "converted_to_feature"
    feature_id: int = Field(..., description="转换到的 feature 编号")


class ClosedResult(BaseModel):
    """无 feature 关闭的处理结果."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["closed"] = "closed"
    reason_type: IssueCloseReason = Field(..., description="关闭原因分类")
    reason: str = Field(..., description="关闭原因说明")


# Discriminated union for result
IssueResult = Annotated[
    Union[ConvertedResult, ClosedResult],
    Field(discriminator="type"),
]


class Issue(BaseModel):
    """对应 .issues/<id>/ISSUE.yaml."""
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_desc(cls, data):
        return migrate_legacy_desc(data)

    id: int = Field(..., ge=1, le=999, description="issue 编号")
    title: str = Field(..., description="目录名（不可改，创建时通过 --slug 决定）")
    user_input: str = Field(..., description="用户原始描述（create 时填，保留原话）")
    summary: Optional[str] = Field(None, max_length=50,
        description="一句话总结（≤50 字）：什么问题/现象+影响；信息收集阶段 PM 提炼写入，不写根因/修复方案")

    # PM 加工后填（信息收集阶段）
    scenario: Optional[str] = Field(None,
        description="问题场景：如何复现（PM 与用户讨论后填）")
    impact: Optional[str] = Field(None,
        description="问题影响：问题点 + 影响范围")

    # QA 诊断产出
    root_cause: Optional[str] = Field(None, description="根因")
    fix_plan: Optional[str] = Field(None,
        description="qa-diagnosis 给的定位结论与修复方向（含问题分析 + 处理方向）")

    # 处理结果（closed 时必填）
    result: Optional[IssueResult] = Field(None,
        description="issue 处理结果（converted_to_feature 或 closed）")
