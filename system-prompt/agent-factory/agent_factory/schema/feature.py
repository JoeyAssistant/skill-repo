# agent_factory/schema/feature.py
"""Feature 模型（对应 .features/<id>/FEATURE.yaml）."""
from __future__ import annotations
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentType(str, Enum):
    """Agent 形态."""
    CLI_ONLY = "cli-only"
    HTTP_API = "http-api"
    HTTP_WEB = "http-web"
    MCP_SERVER = "mcp-server"


class FeatureStatus(str, Enum):
    """Feature 生命周期状态."""
    DRAFT = "draft"
    DESIGNING = "designing"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    QA_REVIEWING = "qa-reviewing"
    DONE = "done"
    CANCELLED = "cancelled"


class Background(BaseModel):
    """需求背景（嵌套）."""
    model_config = ConfigDict(extra="forbid")
    pain_point: Optional[str] = Field(None, description="解决什么痛点")
    benefit: Optional[str] = Field(None, description="带来什么收益")


class ModuleSpec(BaseModel):
    """单个模块的需求规格（spec 按模块 dict 的 value）."""
    model_config = ConfigDict(extra="forbid")
    functions: list[str] = Field(default_factory=list, description="功能、修改点")
    schema: Optional[str] = Field(None, description="data schema")
    interface: Optional[str] = Field(None, description="API / CLI 接口")


class FeatureTestCase(BaseModel):
    """验收用例."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="用例名")
    precondition: str = Field(..., description="前置构造")
    steps: str = Field(..., description="可重复执行的步骤")
    expected: str = Field(..., description="通过判据")


class Feature(BaseModel):
    """对应 .features/<NNN>-<slug>/FEATURE.yaml."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=999, description="feature 编号")
    title: str = Field(..., description="目录名（不可改，创建时通过 --slug 决定）")
    desc: str = Field(..., description="用户原始需求描述（create 时必填）")
    agent_type: AgentType = Field(..., description="Agent 形态")

    background: Optional[Background] = Field(None, description="需求背景（draft 阶段填）")
    spec: dict[str, ModuleSpec] = Field(default_factory=dict,
        description="需求规格，按模块组织（designing 阶段逐模块写入）")
    test_cases: list[FeatureTestCase] = Field(default_factory=list,
        description="验收用例（designing 阶段填）")
