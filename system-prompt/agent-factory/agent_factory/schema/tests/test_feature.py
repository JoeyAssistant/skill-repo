# agent_factory/schema/tests/test_feature.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.feature import AgentType
from agent_factory.schema.feature import Background, Feature, ModuleSpec, FeatureTestCase


# === Background 测试 ===

def test_background_valid():
    bg = Background(pain_point="痛点", benefit="收益")
    assert bg.pain_point == "痛点"
    assert bg.benefit == "收益"


def test_background_fields_optional():
    """Background fields are optional (completeness checked at transition time)."""
    bg = Background()
    assert bg.pain_point is None
    assert bg.benefit is None
    bg2 = Background(pain_point="痛点")
    assert bg2.benefit is None


def test_background_extra_forbidden():
    with pytest.raises(ValidationError):
        Background(pain_point="痛点", benefit="收益", extra="x")


# === ModuleSpec 测试 ===

def test_module_spec_minimal():
    ms = ModuleSpec(functions=["fn1"])
    assert ms.functions == ["fn1"]
    assert ms.schema is None
    assert ms.interface is None


def test_module_spec_full():
    ms = ModuleSpec(functions=["fn1", "fn2"], schema="class X:", interface="| cmd |")
    assert len(ms.functions) == 2
    assert ms.schema == "class X:"
    assert ms.interface == "| cmd |"


def test_module_spec_extra_forbidden():
    with pytest.raises(ValidationError):
        ModuleSpec(functions=[], extra="x")


# === TestCase 测试 ===

def test_test_case_valid():
    tc = FeatureTestCase(name="t1", precondition="p", steps="s", expected="e")
    assert tc.name == "t1"


def test_test_case_missing_field_fails():
    with pytest.raises(ValidationError):
        FeatureTestCase(name="t1", precondition="p", steps="s")  # missing expected


def test_test_case_extra_forbidden():
    with pytest.raises(ValidationError):
        FeatureTestCase(name="t1", precondition="p", steps="s", expected="e", extra="x")


# === Feature 测试 ===

def _valid_feature_kwargs():
    return dict(
        id=1,
        title="001-income-module",
        desc="用户原话：收入管理",
        agent_type=AgentType.CLI_ONLY,
    )


def test_feature_minimal_valid():
    feature = Feature(**_valid_feature_kwargs())
    assert feature.id == 1
    assert feature.title == "001-income-module"
    assert feature.desc == "用户原话：收入管理"
    assert feature.agent_type == AgentType.CLI_ONLY
    assert feature.background is None
    assert feature.spec == {}
    assert feature.test_cases == []


def test_feature_missing_desc_fails():
    kw = _valid_feature_kwargs()
    del kw["desc"]
    with pytest.raises(ValidationError) as exc:
        Feature(**kw)
    errors = exc.value.errors()
    missing = [e["loc"][0] for e in errors if e["type"] == "missing"]
    assert "desc" in missing


def test_feature_with_full_structure():
    kw = _valid_feature_kwargs()
    kw["background"] = Background(pain_point="痛点描述", benefit="收益描述")
    kw["spec"] = {
        "income": ModuleSpec(functions=["录入"], schema="class X:", interface="add"),
        "report": ModuleSpec(functions=["汇总"]),
    }
    kw["test_cases"] = [
        FeatureTestCase(name="用例1", precondition="空数据", steps="执行add", expected="有记录"),
        FeatureTestCase(name="用例2", precondition="有数据", steps="执行list", expected="返回列表"),
    ]
    feature = Feature(**kw)
    assert feature.background is not None
    assert feature.background.pain_point == "痛点描述"
    assert len(feature.spec) == 2
    assert "income" in feature.spec
    assert "report" in feature.spec
    assert len(feature.test_cases) == 2


def test_feature_extra_field_forbidden():
    kw = _valid_feature_kwargs()
    kw["unknown_field"] = "value"
    with pytest.raises(ValidationError) as exc:
        Feature(**kw)
    errors = exc.value.errors()
    assert any(e["type"] == "extra_forbidden" for e in errors)


def test_feature_id_range():
    kw = _valid_feature_kwargs()
    kw["id"] = 0
    with pytest.raises(ValidationError):
        Feature(**kw)
    kw["id"] = 1000
    with pytest.raises(ValidationError):
        Feature(**kw)


def test_feature_agent_type_must_be_enum():
    kw = _valid_feature_kwargs()
    kw["agent_type"] = "unknown-type"
    with pytest.raises(ValidationError):
        Feature(**kw)


def test_feature_status_enum_values():
    """7 states: draft/designing/approved/implementing/qa-reviewing/done/cancelled."""
    from agent_factory.schema.feature import FeatureStatus
    assert len(FeatureStatus) == 7
    assert FeatureStatus.DRAFT.value == "draft"
    assert FeatureStatus.DESIGNING.value == "designing"
    assert FeatureStatus.APPROVED.value == "approved"
    assert FeatureStatus.IMPLEMENTING.value == "implementing"
    assert FeatureStatus.QA_REVIEWING.value == "qa-reviewing"
    assert FeatureStatus.DONE.value == "done"
    assert FeatureStatus.CANCELLED.value == "cancelled"
