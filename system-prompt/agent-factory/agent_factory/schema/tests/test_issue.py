# agent_factory/schema/tests/test_issue.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.issue import Issue


def _valid_issue_kwargs():
    return dict(
        id=1,
        title="登录页面点击提交后崩溃",
        scenario="现象：登录页面点击提交后页面崩溃。\n复现步骤：1. 打开 /login 2. 输入 admin/123456 3. 点击登录",
        impact="问题点：login.py L42 未做空值判断。\n影响范围：所有用户无法登录，P1。",
    )


def test_issue_minimal_valid():
    issue = Issue(**_valid_issue_kwargs())
    assert issue.id == 1
    assert issue.root_cause is None
    assert issue.fix_plan is None
    assert issue.action is None
    assert issue.fix is None
    assert issue.resolution is None


def test_issue_missing_required_field_fails():
    with pytest.raises(ValidationError) as exc:
        Issue(id=1, title="...")
    errors = exc.value.errors()
    missing = [e["loc"][0] for e in errors if e["type"] == "missing"]
    for field in ["scenario", "impact"]:
        assert field in missing


def test_issue_extra_field_forbidden():
    kw = _valid_issue_kwargs()
    kw["unknown_field"] = "value"
    with pytest.raises(ValidationError) as exc:
        Issue(**kw)
    errors = exc.value.errors()
    assert any(e["type"] == "extra_forbidden" for e in errors)


def test_issue_with_qa_diagnosis():
    kw = _valid_issue_kwargs()
    kw["root_cause"] = "login.py L42 未做空值判断。"
    kw["fix_plan"] = "方案 A：前端做 token 存在性判断。"
    kw["action"] = "direct-fix"
    issue = Issue(**kw)
    assert issue.root_cause.startswith("login.py")
    assert "方案 A" in issue.fix_plan
    assert issue.action == "direct-fix"


def test_issue_with_full_lifecycle():
    kw = _valid_issue_kwargs()
    kw["root_cause"] = "..."
    kw["fix_plan"] = "..."
    kw["action"] = "direct-fix"
    kw["fix"] = "Changed Files: cli/login.py (+5)"
    kw["resolution"] = "direct-fix"
    issue = Issue(**kw)
    assert issue.resolution == "direct-fix"


def test_issue_action_field_valid_values():
    """action field accepts direct-fix and convert-to-feature."""
    issue = Issue(
        id=1, title="...", scenario="...", impact="...",
        root_cause="...", fix_plan="...",
        action="direct-fix",
    )
    assert issue.action == "direct-fix"

    issue2 = Issue(
        id=1, title="...", scenario="...", impact="...",
        root_cause="...", fix_plan="...",
        action="convert-to-feature",
    )
    assert issue2.action == "convert-to-feature"


def test_issue_action_field_invalid_value_rejected():
    """action field rejects invalid values."""
    with pytest.raises(ValidationError):
        Issue(
            id=1, title="...", scenario="...", impact="...",
            root_cause="...", fix_plan="...",
            action="invalid-value",
        )


def test_issue_id_range():
    kw = _valid_issue_kwargs()
    kw["id"] = 0
    with pytest.raises(ValidationError):
        Issue(**kw)
    kw["id"] = 1000
    with pytest.raises(ValidationError):
        Issue(**kw)
