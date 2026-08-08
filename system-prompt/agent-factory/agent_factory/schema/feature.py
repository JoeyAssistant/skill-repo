# agent_factory/schema/feature.py
"""Feature 模型（对应 .features/<id>/REQUIREMENTS.yaml）."""
from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_factory.schema.enums import AgentType, DecisionStatus


class Option(BaseModel):
    """决策选项."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[A-Z]$", description="选项标识，单字母 A-Z（必须大写）")
    name: str = Field(..., description="选项名称")
    pros: str = Field(..., description="优点")
    cons: str = Field(..., description="缺点")
    impact: Optional[str] = Field(None, description="选了这个选项的实际影响")


class Decision(BaseModel):
    """PM 与用户的决策记录."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^dec-[1-9]\d*$", description="决策标识，如 dec-1（从 1 开始）")
    question: str = Field(..., description="一句话问题陈述")
    background: str = Field(..., description="背景与触发场景")
    options: list[Option] = Field(..., min_length=2, max_length=5,
                                  description="2-5 个选项")
    recommendation: str = Field(..., description="推荐的 option id (A/B/C)")
    rationale: str = Field(..., description="推荐理由")
    fallback_condition: Optional[str] = Field(None,
        description="什么情况下应选其他选项")
    status: DecisionStatus = Field(DecisionStatus.OPEN, description="决策状态（open=待定 / closed=已选定）")

    @model_validator(mode="after")
    def check_recommendation_in_options(self):
        ids = [o.id for o in self.options]
        if self.recommendation not in ids:
            raise ValueError(
                f"recommendation '{self.recommendation}' not in option ids: {ids}"
            )
        return self


class Feature(BaseModel):
    """对应 .features/<id>/REQUIREMENTS.yaml."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=999, description="feature 编号")
    title: str = Field(..., description="一句话标题，人读展示")
    agent_type: AgentType = Field(..., description="Agent 形态（cli-only/http-api/http-web/mcp-server）")

    problem: str = Field(..., description="解决什么问题")
    benefit: str = Field(..., description="创造什么价值")
    description: str = Field(...,
        description="详细需求描述（含用户、场景、功能），自由文本")

    data_schema: Optional[str] = Field(None,
        description="数据契约（designing 阶段补，python dataclass + enum 代码块）")
    interfaces: Optional[str] = Field(None,
        description="接口清单（按 agent_type 写 CLI / API / MCP 内容）")

    acceptance_cases: str = Field("", description="验收 Case，自由文本")
    decisions: list[Decision] = Field(default_factory=list,
        description="PM 与用户的决策记录")
