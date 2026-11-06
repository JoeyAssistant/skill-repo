# agent_factory/schema/compat.py
"""Legacy YAML field compatibility."""
from __future__ import annotations
from typing import Any


def migrate_legacy_desc(data: Any) -> Any:
    """Map the legacy `desc` key to `user_input`.

    Historical ISSUE.yaml / FEATURE.yaml files use `desc`; new files use
    `user_input`. Reads accept both, writes always emit `user_input`.
    When both keys exist, `user_input` wins.
    """
    if not isinstance(data, dict) or "desc" not in data:
        return data
    data = dict(data)
    if "user_input" not in data:
        data["user_input"] = data.pop("desc")
    else:
        data.pop("desc")
    return data


def migrate_legacy_issue(data: Any) -> Any:
    """Migrate historical ISSUE.yaml field layouts to the current model.

    - `desc` → `user_input`
    - `evidence` → `analysis`（更名后语义不变，仅展示侧默认隐藏）
    - `fix_plan` 字符串 → `fix_plan.permanent_fix`（修复方案拆成止血/根治两档）
    - `repro_steps` 丢弃（字段已下线；历史文件仍带该键，extra="forbid" 会拒绝）

    Reads accept both layouts; writes always emit the current one.
    """
    data = migrate_legacy_desc(data)
    if not isinstance(data, dict):
        return data
    data = dict(data)

    if "analysis" not in data and "evidence" in data:
        data["analysis"] = data.pop("evidence")
    else:
        data.pop("evidence", None)

    fix_plan = data.get("fix_plan")
    if isinstance(fix_plan, str):
        data["fix_plan"] = {"permanent_fix": fix_plan} if fix_plan.strip() else None

    data.pop("repro_steps", None)
    return data
