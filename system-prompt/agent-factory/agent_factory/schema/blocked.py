"""BlockedRecord 模型（对应 .features/<id>/BLOCKED.yaml 或 .issues/<id>/BLOCKED.yaml）."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BlockedRecord(BaseModel):
    """阻塞记录. feature 或 issue blocked 时创建."""
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(...,
        description="阻塞原因（含类型 / 来源 / 日期，自由文本）")
    action: str = Field(...,
        description="需要用户提供的信息或操作")
