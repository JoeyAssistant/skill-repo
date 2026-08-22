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


class Observation(BaseModel):
    """E2E 观测点（可观测的断言）。"""
    model_config = ConfigDict(extra="forbid")
    check: str = Field(..., description="测试验证点（可 grep / 可查的观测）")
    expect: str = Field(..., description="预期结果（断言）")


class E2ETestCase(BaseModel):
    """E2E 验收用例（可构造、可观测、可运行）。"""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="用例名")
    precondition: str = Field(..., description="前置条件")
    inputs: dict = Field(default_factory=dict, description="测试输入（可构造参数 key: value）")
    steps: list[str] = Field(default_factory=list, description="测试步骤（可运行，逐步）")
    observations: list[Observation] = Field(default_factory=list,
        description="观测点列表（可观测，每条 {check, expect}）")


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
    e2e_test_cases: list[E2ETestCase] = Field(default_factory=list,
        description="E2E 验收用例（designing 阶段逐条与用户讨论后填入）")
