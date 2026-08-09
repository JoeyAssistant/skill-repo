# agent_factory/schema/validate.py
"""YAML schema validation utilities.

NOTE: Standalone validate CLI has been removed. Validation happens
inside cli/ write commands (load → pydantic validate → write).
This module exports utility functions reused by cli/common.py and cli/* commands.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError


def load_yaml(path: Path) -> dict:
    """Load YAML file as dict."""
    with path.open() as f:
        return yaml.safe_load(f) or {}


def format_validation_error(path: Path, exc: ValidationError) -> str:
    """Format pydantic ValidationError for stderr output."""
    lines = [f"❌ {path}"]
    for err in exc.errors():
        loc = "."".join(str(x) for x in err["loc"])
        lines.append(f"  {loc}: {err['msg']}")
    return "\n".join(lines)
