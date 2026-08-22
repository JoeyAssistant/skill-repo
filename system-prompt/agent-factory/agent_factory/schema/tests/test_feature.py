# agent_factory/schema/tests/test_feature.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.feature import AgentType
from agent_factory.schema.feature import Background, E2ETestCase, Feature, ModuleSpec, Observation


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


# === E2ETestCase 测试 ===

def test_e2e_test_case_valid():
    tc = E2ETestCase(
        name="t1", precondition="p",
        inputs={"device_name": "XYANGS-RT-AS5PR-008"},
        steps=["step1", "step2"],
        observations=[Observation(check="日志行", expect="含 xxx")],
    )
    assert tc.name == "t1"
    assert isinstance(tc.steps, list) and len(tc.steps) == 2
    assert len(tc.observations) == 1


def test_observation_missing_expect_fails():
    with pytest.raises(ValidationError):
        Observation(check="x")  # missing expect


def test_e2e_test_case_extra_forbidden():
    with pytest.raises(ValidationError):
        E2ETestCase(name="t1", precondition="p", steps=["s"], observations=[], extra="x")


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
    assert feature.e2e_test_cases == []


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
    kw["e2e_test_cases"] = [
        E2ETestCase(name="用例1", precondition="空数据", steps=["执行add"], observations=[Observation(check="add 结果", expect="有记录")]),
        E2ETestCase(name="用例2", precondition="有数据", steps=["执行list"], observations=[Observation(check="list 结果", expect="返回列表")]),
    ]
    feature = Feature(**kw)
    assert feature.background is not None
    assert feature.background.pain_point == "痛点描述"
    assert len(feature.spec) == 2
    assert "income" in feature.spec
    assert "report" in feature.spec
    assert len(feature.e2e_test_cases) == 2


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
