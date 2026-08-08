# agent_factory/schema/tests/test_blocked.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.blocked import BlockedRecord


def test_blocked_record_valid():
    rec = BlockedRecord(
        reason="designing 阶段卡住（tech-feasibility）。需要确认 MCP server 是否支持流式响应。",
        action="调度 POC subagent 验证 MCP 流式能力；或用户决定改用 http-api + SSE。",
    )
    assert "tech-feasibility" in rec.reason
    assert "POC" in rec.action


def test_blocked_record_missing_required_field_fails():
    with pytest.raises(ValidationError) as exc:
        BlockedRecord(reason="...")
    errors = exc.value.errors()
    missing = [e["loc"][0] for e in errors if e["type"] == "missing"]
    assert "action" in missing


def test_blocked_record_extra_field_forbidden():
    with pytest.raises(ValidationError):
        BlockedRecord(
            reason="...", action="...", extra="x",
        )
