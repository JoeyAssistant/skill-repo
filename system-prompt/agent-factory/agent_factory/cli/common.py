"""Shared utilities for CLI commands."""
from __future__ import annotations

from pathlib import Path
from enum import Enum
from typing import Any, Optional

import yaml
from pydantic import BaseModel

from agent_factory.schema import FeatureIndex, IssueIndex


def _convert_enums_to_strings(obj: Any) -> Any:
    """Recursively convert Enum objects to their string values."""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _convert_enums_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_enums_to_strings(item) for item in obj]
    return obj


def load_yaml(path: Path) -> dict:
    """Load YAML file as dict."""
    with path.open() as f:
        return yaml.safe_load(f) or {}


def dump_yaml(path: Path, data: Any) -> None:
    """Dump data to YAML file (Unicode preserved, sort_keys=False)."""
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json", by_alias=True, exclude_none=True)
    else:
        # Handle nested enums in dicts/lists
        data = _convert_enums_to_strings(data)
    with path.open("w") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def find_feature_dir(feature_id: int) -> Path:
    """Find .features/<id>/ directory. Raise FileNotFoundError if missing."""
    p = Path(".features") / str(feature_id)
    if not p.exists():
        raise FileNotFoundError(f"Feature {feature_id} not found: {p}")
    return p


def find_issue_dir(issue_id: int) -> Path:
    """Find .issues/<id>/ directory."""
    p = Path(".issues") / str(issue_id)
    if not p.exists():
        raise FileNotFoundError(f"Issue {issue_id} not found: {p}")
    return p


def format_error(error_type: str, detail: str, context: Optional[str] = None) -> str:
    """Format error message for stderr output."""
    lines = [f"Error: {error_type}", f"  {detail}"]
    if context:
        lines.append(f"  Context: {context}")
    return "\n".join(lines)


def next_feature_id() -> int:
    """Get next feature id from .features/index.yaml (max + 1)."""
    idx_path = Path(".features") / "index.yaml"
    if not idx_path.exists():
        return 1
    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    if not idx.features:
        return 1
    return max(item.id for item in idx.features) + 1


def next_issue_id() -> int:
    """Get next issue id from .issues/index.yaml (max + 1)."""
    idx_path = Path(".issues") / "index.yaml"
    if not idx_path.exists():
        return 1
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    if not idx.issues:
        return 1
    return max(item.id for item in idx.issues) + 1
