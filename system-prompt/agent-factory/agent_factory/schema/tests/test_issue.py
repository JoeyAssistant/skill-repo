# agent_factory/schema/tests/test_issue.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.issue import (
    Issue, BugfixResult, FeatureRequestResult,
)
from agent_factory.schema.issue import IssueStatus


def test_issue_minimal_valid():
    """Minimal Issue: id + title + desc (其他 Optional)."""
    issue = Issue(id=1, title="001-test", desc="用户原始描述")
    assert issue.id == 1
    assert issue.desc == "用户原始描述"
    assert issue.scenario is None
    assert issue.impact is None
    assert issue.root_cause is None
    assert issue.fix_plan is None
    assert issue.result is None


def test_issue_missing_desc_fails():
    with pytest.raises(ValidationError) as exc:
        Issue(id=1, title="001-test")
    errors = exc.value.errors()
    missing = [e["loc"][0] for e in errors if e["type"] == "missing"]
    assert "desc" in missing


def test_issue_extra_field_forbidden():
    with pytest.raises(ValidationError):
        Issue(id=1, title="001-test", desc="x", extra="y")


def test_bugfix_result_valid():
    r = BugfixResult(fix_desc="改了 x.py", verification="git show 通过 + 测试 8 passed")
    assert r.type == "bugfix"


def test_feature_request_result_valid():
    r = FeatureRequestResult(feature_id=70)
    assert r.type == "feature_request"


def test_issue_with_bugfix_result():
    issue = Issue(
        id=1, title="001-test", desc="x",
        result=BugfixResult(fix_desc="...", verification="..."),
    )
    assert issue.result.type == "bugfix"
    assert issue.result.fix_desc == "..."


def test_issue_with_feature_request_result():
    issue = Issue(
        id=1, title="001-test", desc="x",
        result=FeatureRequestResult(feature_id=5),
    )
    assert issue.result.type == "feature_request"
    assert issue.result.feature_id == 5


def test_issue_status_enum_renamed():
    """IssueStatus 不再有 TRIAGING，改为 IN_PROGRESS."""
    assert IssueStatus.IN_PROGRESS.value == "in_progress"
    # 验证 TRIAGING 不存在
    assert not hasattr(IssueStatus, "TRIAGING")


def test_issue_id_range():
    with pytest.raises(ValidationError):
        Issue(id=0, title="...", desc="...")
    with pytest.raises(ValidationError):
        Issue(id=1000, title="...", desc="...")
