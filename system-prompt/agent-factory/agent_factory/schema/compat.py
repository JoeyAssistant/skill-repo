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
