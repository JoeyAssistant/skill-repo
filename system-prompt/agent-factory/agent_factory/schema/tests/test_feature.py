# agent_factory/schema/tests/test_feature.py
import pytest
from pydantic import ValidationError

from agent_factory.schema.enums import AgentType, DecisionStatus
from agent_factory.schema.feature import Feature, Decision, Option


# === Option 测试 ===

def test_option_valid():
    opt = Option(id="A", name="方案 A", pros="优点", cons="缺点")
    assert opt.id == "A"
    assert opt.impact is None


def test_option_id_must_be_single_uppercase():
    with pytest.raises(ValidationError):
        Option(id="AA", name="...", pros="...", cons="...")
    with pytest.raises(ValidationError):
        Option(id="1", name="...", pros="...", cons="...")
    with pytest.raises(ValidationError):
        Option(id="a", name="...", pros="...", cons="...")


def test_option_extra_field_forbidden():
    with pytest.raises(ValidationError):
        Option(id="A", name="...", pros="...", cons="...", extra="x")


# === Decision 测试 ===

def _valid_decision_kwargs():
    return dict(
        id="dec-1",
        question="stdio 还是 sse？",
        background="生产需要远程访问，本地用 stdio 最简。",
        options=[
            Option(id="A", name="stdio", pros="本地最简", cons="无法远程"),
            Option(id="B", name="sse", pros="支持远程", cons="需要部署"),
        ],
        recommendation="A",
        rationale="优先支持本地开发体验，远程访问可后续加。",
    )


def test_decision_valid():
    dec = Decision(**_valid_decision_kwargs())
    assert dec.id == "dec-1"
    assert dec.status == DecisionStatus.OPEN  # 默认值


def test_decision_id_pattern():
    kw = _valid_decision_kwargs()
    kw["id"] = "oq-1"  # 旧前缀，应拒绝
    with pytest.raises(ValidationError):
        Decision(**kw)

    kw["id"] = "dec-abc"  # 非数字
    with pytest.raises(ValidationError):
        Decision(**kw)


def test_decision_options_min_length_2():
    kw = _valid_decision_kwargs()
    kw["options"] = [
        Option(id="A", name="...", pros="...", cons="..."),
    ]  # 只 1 个
    with pytest.raises(ValidationError) as exc:
        Decision(**kw)
    assert "too_short" in str(exc.value) or "at least 2" in str(exc.value).lower()


def test_decision_options_max_length_5():
    kw = _valid_decision_kwargs()
    kw["options"] = [
        Option(id=letter, name="...", pros="...", cons="...")
        for letter in "ABCDEF"
    ]  # 6 个
    with pytest.raises(ValidationError):
        Decision(**kw)


def test_decision_recommendation_must_be_in_options():
    kw = _valid_decision_kwargs()
    kw["recommendation"] = "C"  # 不在 options
    with pytest.raises(ValidationError) as exc:
        Decision(**kw)
    assert "not in option" in str(exc.value).lower()


# === Feature 测试 ===

def _valid_feature_kwargs():
    return dict(
        id=1,
        title="收入管理模块",
        agent_type=AgentType.CLI_ONLY,
        problem="无法看到完整财务画像。",
        benefit="集中记录收入流水。",
        description="个人用户月底复盘月度净收支。",
    )


def test_feature_minimal_valid():
    feature = Feature(**_valid_feature_kwargs())
    assert feature.id == 1
    assert feature.agent_type == AgentType.CLI_ONLY
    assert feature.data_schema is None
    assert feature.interfaces is None
    assert feature.acceptance_cases == ""
    assert feature.decisions == []


def test_feature_missing_required_field_fails():
    with pytest.raises(ValidationError) as exc:
        Feature(id=1, title="...")
    errors = exc.value.errors()
    missing = [e["loc"][0] for e in errors if e["type"] == "missing"]
    for field in ["agent_type", "problem", "benefit", "description"]:
        assert field in missing


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


def test_feature_with_decision():
    kw = _valid_feature_kwargs()
    kw["decisions"] = [Decision(**_valid_decision_kwargs())]
    feature = Feature(**kw)
    assert len(feature.decisions) == 1
    assert feature.decisions[0].id == "dec-1"


def test_feature_agent_type_must_be_enum():
    kw = _valid_feature_kwargs()
    kw["agent_type"] = "unknown-type"
    with pytest.raises(ValidationError):
        Feature(**kw)
