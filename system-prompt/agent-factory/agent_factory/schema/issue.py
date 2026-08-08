# agent_factory/schema/issue.py
"""Issue 模型（对应 .issues/<id>/ISSUE.yaml）."""
from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Issue(BaseModel):
    """对应 .issues/<id>/ISSUE.yaml（原 NOTES.md 改名）."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, le=999, description="issue 编号")
    title: str = Field(..., description="一句话标题")

    # 报告字段（PM 创建时填）
    scenario: str = Field(...,
        description="问题场景：如何复现（feature-request 则是使用场景）")
    impact: str = Field(...,
        description="问题影响：问题点 + 影响范围")

    # QA 诊断（QA 填，PM review fix_suggestion 后才开发）
    root_cause: Optional[str] = Field(None, description="根因（QA 诊断产出）")
    fix_suggestion: Optional[str] = Field(None,
        description="修复方案（PM review 后才开发）")

    # 修复记录（developer 填）
    fix: Optional[str] = Field(None,
        description="修复记录：changed files / regression test")

    # 处理结果（PM 填）
    resolution: Optional[str] = Field(None,
        description="处理结果：direct-fix / converted-to-feature #NNN")
