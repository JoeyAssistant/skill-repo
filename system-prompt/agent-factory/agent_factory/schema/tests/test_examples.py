"""所有 example YAML 必须能通过对应 schema 校验.

防止 schema 改动后 examples 过期（如 2026-08-14 issue_index.yaml 漏改 type 字段
导致用户项目 CLI 崩溃的事故）。
"""
from pathlib import Path

import pytest
import yaml

from agent_factory.schema import (
    Feature,
    FeatureIndex,
    Issue,
    IssueIndex,
)

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

CASES = [
    ("issue.yaml", Issue),
    ("feature.yaml", Feature),
    ("issue_index.yaml", IssueIndex),
    ("feature_index.yaml", FeatureIndex),
]


@pytest.mark.parametrize("filename,model", CASES)
def test_example_validates_against_schema(filename: str, model) -> None:
    path = EXAMPLES_DIR / filename
    data = yaml.safe_load(path.read_text())
    model.model_validate(data)  # raises ValidationError if stale
