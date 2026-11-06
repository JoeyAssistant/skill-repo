# agent_factory/schema/issue.py
"""Issue 模型（对应 .issues/<id>/ISSUE.yaml）."""
from __future__ import annotations
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_factory.schema.compat import migrate_legacy_issue


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


class AnalysisType(str, Enum):
    """分析步骤的依据类型."""
    CODE = "code"
    LOG = "log"
    DATA = "data"


class AnalysisItem(BaseModel):
    """有序分析过程的一步（agent 使用，默认不展示给人）."""
    model_config = ConfigDict(extra="forbid")
    step: int = Field(..., ge=1, description="推理顺序，从 1 递增")
    claim: str = Field(...,
        description="这一步得出的断言（一句话）；支撑/排除、推断边界都写在这里")
    type: AnalysisType = Field(..., description="依据类型：code / log / data")
    locator: str = Field(...,
        description="位置：code 用 path:line @ <commit SHA>；log/data 用绝对路径 + 行号")
    snippet: str = Field(...,
        description="locator 处的原文片段，不改写；统计结论放 claim")


class FixPlan(BaseModel):
    """修复方案：止血档与根治档并列，各自独立可拍板.

    两个子字段在模型层都可空：两档可能分先后写入，任一时刻的中间态都要能通过校验。
    ``permanent_fix`` 的必填性由 convert / close(no_action) 的门禁保证，而不是这里。
    """
    model_config = ConfigDict(extra="forbid")
    quick_fix: Optional[str] = Field(None,
        description="止血方案：目标 / 改什么 / 用户感受 / 代价 / 不解决什么 / 上线门槛；无止血需求时留空")
    permanent_fix: Optional[str] = Field(None,
        description="根治方案（convert / close(no_action) 前必填）：方向 + 关键改动点 + 不做 + 上线门槛；不写文件、函数、行号")


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
    def _accept_legacy(cls, data):
        return migrate_legacy_issue(data)

    id: int = Field(..., ge=1, le=999, description="issue 编号")
    title: str = Field(..., description="目录名（不可改，创建时通过 --slug 决定）")
    user_input: str = Field(...,
        description="用户原始输入：直接上报的问题保留原话；多轮讨论产出的问题由 PM 总结成一段")
    summary: Optional[str] = Field(None, max_length=50,
        description="一句话总结（≤50 字）：什么问题/现象+影响；信息收集阶段 PM 提炼写入，不写根因/修复方案")

    # PM 加工后填（信息收集阶段）
    scenario: Optional[str] = Field(None,
        description="用户使用场景与操作：谁 + 在什么情况下 + 系统呈现什么状态；≤200 字；不写原因、代价、代码路径（PM 信息收集，用户确认后写入）")
    impact: Optional[str] = Field(None,
        description="损害与范围：丢了什么 + 影响多少 + 多严重 + 频率；不复述现象与流程")
    flow: Optional[str] = Field(None,
        description="流程与问题点：用户做了什么 → 系统依次做了什么（每步耗时/结果、标正常/异常），并指认问题点在哪一步；自由文本，不写代码细节")

    # QA 诊断产出（提案，PM 确认后写入）
    root_cause: Optional[str] = Field(None,
        description="根因结论：回答问题点为什么如此；单段按可读宽度换行；不写证据、文件路径、推理过程")
    analysis: Optional[list[AnalysisItem]] = Field(None,
        description="分析过程：agent 使用，默认不展示给人；顺序即推理顺序，被排除的假设也作为一步写入")
    log_gap: Optional[str] = Field(None,
        description="维测日志缺口：缺了什么信息、导致判断不了什么、应在哪里补；日志充足时写 N/A")
    fix_plan: Optional[FixPlan] = Field(None,
        description="修复方案：quick_fix（止血，可空）+ permanent_fix（根治，必填）")

    # 处理结果（closed 时必填）
    result: Optional[IssueResult] = Field(None,
        description="issue 处理结果（converted_to_feature 或 closed）")
