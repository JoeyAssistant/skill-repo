# agent_factory/schema/feature.py
"""Feature 模型（对应 .features/<id>/FEATURE.yaml）."""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agent_factory.schema.compat import migrate_legacy_desc


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
    """单个模块的需求规格（spec 按 module dict 的 value）."""
    model_config = ConfigDict(extra="forbid")
    functions: list[str] = Field(default_factory=list, description="功能、修改点")


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
    cleanup: Union[list[str], Literal["N/A"]] = Field(default_factory=list,
        description="清理步骤（删除 /tmp 测试文件、停止服务、恢复测试数据等）；不需要/不涉及清理时写 \"N/A\"。E2E 用例必填")


class WorktreeInfo(BaseModel):
    """feature 绑定的 git worktree（agent-factory worktree new 时由 CLI 写入）."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="worktree 目录名（.worktrees/ 下）")
    branch: str = Field(..., description="绑定的分支名")
    path: str = Field(..., description="相对主仓根的路径")
    base: Optional[str] = Field(None,
        description="基线分支（创建时的 --base 值）；历史记录可能缺失")


FeatureSubagent = Literal["developer", "qa", "poc"]
SubagentResult = Literal["complete", "pass", "fail", "lock_busy", "interrupted"]


class SubagentRun(BaseModel):
    """一条归属于 feature 的 subagent 调度记录。"""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, strict=True, description="feature 内的执行编号")
    agent: FeatureSubagent
    task: str = Field(..., min_length=1, description="本次任务描述")
    dispatched_at: datetime = Field(..., description="PM 调度时间（UTC）")
    result: Optional[SubagentResult] = None
    duration_s: Optional[int] = Field(None, ge=0, strict=True,
        description="subagent 实测总耗时；未知时为空，不按调度时间估算")

    @field_validator("task")
    @classmethod
    def _task_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task must not be blank")
        return value

    @field_validator("dispatched_at")
    @classmethod
    def _utc_timestamp(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("dispatched_at must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def _pending_duration_unknown(self):
        if self.result is None and self.duration_s is not None:
            raise ValueError("unfinished run must have duration_s=null")
        return self


class Feature(BaseModel):
    """对应 .features/<NNN>-<slug>/FEATURE.yaml."""
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_desc(cls, data):
        return migrate_legacy_desc(data)

    id: int = Field(..., ge=1, le=999, description="feature 编号")
    title: str = Field(..., description="目录名（不可改，创建时通过 --slug 决定）")
    user_input: str = Field(..., description="用户原始需求描述（create 时必填）")
    summary: Optional[str] = Field(None, max_length=50,
        description="一句话总结（≤50 字）：以「支持 xxx 功能 / 解决 xxx 问题」开头，一眼明确做什么；需求收集阶段 PM 提炼，经用户确认后写入")

    background: Optional[Background] = Field(None, description="需求背景（draft 阶段填）")
    source_issue: Optional[int] = Field(None, ge=1, le=999,
        description="来源 issue 编号（由 issue 转换而来时写入）")
    spec: dict[str, ModuleSpec] = Field(default_factory=dict,
        description="需求规格，按模块组织（designing 阶段逐模块写入）")
    e2e_test_cases: list[E2ETestCase] = Field(default_factory=list,
        description="E2E 验收用例（designing 阶段逐条与用户讨论后填入；无 E2E 场景的需求可为空）")
    deploy: list[str] = Field(default_factory=list,
        description="上线变更清单：代码合入后需人工完成的操作，一条一行，写清「做什么 + 怎么算完成」；无则为空列表")
    # 父子关联（拆分产生）：由 CLI 在 `feature new --parent` 时一次写入，之后不变
    parent: Optional[int] = Field(None, ge=1, le=999,
        description="父 feature 编号（拆分出的子 feature 才有；权威字段）")
    children: list[int] = Field(default_factory=list,
        description="子 feature 编号列表（拆分出的父 feature 才有；派生视图，权威是子的 parent）")
    worktree: Optional[WorktreeInfo] = Field(None,
        description="绑定的 worktree（worktree new 时写入，worktree remove 时清除）")
    subagent_runs: list[SubagentRun] = Field(default_factory=list,
        description="每次 subagent 调度一条记录；由 PM 经 CLI 创建和补全")

    @model_validator(mode="after")
    def _unique_subagent_run_ids(self):
        ids = [run.id for run in self.subagent_runs]
        if len(ids) != len(set(ids)):
            raise ValueError("subagent_runs ids must be unique within a feature")
        return self
