# agent_factory/schema/tests/test_cli_feature.py
import pytest
import yaml
from pathlib import Path
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def test_feature_new_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Initialize empty index
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "收入管理",
        "--slug", "income-module",
        "--user-input", "用户原话：我想记收入",
        "--priority", "P1",
    ])
    assert result.exit_code == 0, result.output
    assert "Created feature 1" in result.output
    assert "001-income-module" in result.output

    # FEATURE.yaml created with slug-named directory
    feat = tmp_path / ".features" / "001-income-module" / "FEATURE.yaml"
    assert feat.exists()
    data = load_yaml(feat)
    assert data["id"] == 1
    assert data["title"] == "001-income-module"
    assert data["user_input"] == "用户原话：我想记收入"

    # Index updated
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 1
    assert idx["features"][0]["id"] == 1
    assert idx["features"][0]["title"] == "001-income-module"
    assert idx["features"][0]["status"] == "draft"
    assert idx["features"][0]["priority"] == "P1"


def test_feature_new_requires_desc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "X",
        "--slug", "x",
    ])
    assert result.exit_code != 0  # --user-input is required


def test_feature_new_invalid_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "X",
        "--slug", "Invalid_Slug",
        "--user-input", "test input",
    ])
    assert result.exit_code == 4  # InvalidSlug


def test_feature_new_slug_must_start_with_letter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "X",
        "--slug", "123-abc",
        "--user-input", "test",
    ])
    assert result.exit_code == 4


def test_feature_new_default_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "X", "--slug", "x", "--user-input", "test input"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P2"  # default


def test_feature_new_with_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new",
        "--title", "收入管理",
        "--slug", "income-module",
        "--user-input", "用户原话：我想记收入",
        "--summary", "解决看不到净收支的问题，新增收入模块，方案是录入+按月汇总",
    ])
    assert result.exit_code == 0, result.output

    data = load_yaml(tmp_path / ".features" / "001-income-module" / "FEATURE.yaml")
    assert data["summary"] == "解决看不到净收支的问题，新增收入模块，方案是录入+按月汇总"


def test_feature_new_without_summary_is_unchanged(tmp_path, monkeypatch):
    """回归：不传 --summary 时不写 summary 键。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "X", "--slug", "x", "--user-input", "d"])
    assert result.exit_code == 0, result.output

    data = load_yaml(tmp_path / ".features" / "001-x" / "FEATURE.yaml")
    assert data.get("summary") is None


def test_feature_new_increments_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "B", "--slug", "b", "--user-input", "test"])
    assert result.exit_code == 0
    assert "Created feature 2" in result.output
    assert "002-b" in result.output


def test_feature_set_desc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "user_input", "新的需求描述",
    ])
    assert result.exit_code == 0, result.output
    assert "Updated feature 1" in result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["user_input"] == "新的需求描述"


def test_feature_set_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "summary",
        "解决看不到净收支的问题，新增收入模块，方案是录入+按月汇总",
    ])
    assert result.exit_code == 0, result.output
    assert "Updated feature 1" in result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["summary"] == "解决看不到净收支的问题，新增收入模块，方案是录入+按月汇总"


def test_feature_set_background_sub(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "background.pain_point", "现有系统无法记收入",
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["background"]["pain_point"] == "现有系统无法记收入"


def test_feature_set_background_whole(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    bg_file = tmp_path / "bg.yaml"
    bg_file.write_text(yaml.safe_dump({"pain_point": "痛点内容", "benefit": "收益内容"}))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "background", "--file", str(bg_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["background"]["pain_point"] == "痛点内容"
    assert feat["background"]["benefit"] == "收益内容"


def test_feature_set_spec_module_upsert(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    spec_file = tmp_path / "income.yaml"
    spec_file.write_text(yaml.safe_dump({
        "functions": ["录入收入", "查询收入"],
    }))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "spec.income", "--file", str(spec_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert "income" in feat["spec"]
    assert feat["spec"]["income"]["functions"] == ["录入收入", "查询收入"]

    # Upsert: write again with different content
    spec_file2 = tmp_path / "income2.yaml"
    spec_file2.write_text(yaml.safe_dump({
        "functions": ["仅录入"],
    }))
    result = runner.invoke(main, [
        "feature", "set", "1", "spec.income", "--file", str(spec_file2),
    ])
    assert result.exit_code == 0, result.output
    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["spec"]["income"]["functions"] == ["仅录入"]


def test_feature_set_spec_module_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature_with_spec(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "spec.income", "--remove",
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert "income" not in feat["spec"]


def test_feature_set_spec_module_remove_nonexistent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "spec.nonexistent", "--remove",
    ])
    assert result.exit_code == 2  # NotFound


def test_feature_set_e2e_test_cases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    tc_file = tmp_path / "cases.yaml"
    tc_file.write_text(yaml.safe_dump([
        {"name": "用例1", "precondition": "空", "inputs": {"project": "XYANGS_RT"}, "steps": ["触发诊断"], "observations": [{"check": "日志行", "expect": "含 xxx"}], "cleanup": ["rm -f /tmp/qa-1.json"]},
        {"name": "用例2", "precondition": "有数据", "inputs": {}, "steps": ["查询"], "observations": [{"check": "结果", "expect": "返回列表"}], "cleanup": ["停止 backend 服务"]},
    ]))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "e2e_test_cases", "--file", str(tc_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert len(feat["e2e_test_cases"]) == 2
    assert feat["e2e_test_cases"][0]["name"] == "用例1"
    assert feat["e2e_test_cases"][0]["cleanup"] == ["rm -f /tmp/qa-1.json"]


def test_feature_set_e2e_test_cases_requires_cleanup(tmp_path, monkeypatch):
    """每条 E2E 用例必须声明非空 cleanup，否则拒绝写入。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    tc_file = tmp_path / "cases.yaml"
    tc_file.write_text(yaml.safe_dump([
        {"name": "用例1", "precondition": "空", "steps": ["执行"], "observations": [{"check": "x", "expect": "y"}]},
    ]))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "e2e_test_cases", "--file", str(tc_file),
    ])
    assert result.exit_code == 1
    assert "cleanup 为空" in result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert "e2e_test_cases" not in feat or feat["e2e_test_cases"] == []


def test_feature_set_e2e_test_cases_accepts_na_cleanup(tmp_path, monkeypatch):
    """不需要/不涉及清理时，cleanup 允许显式写 "N/A"。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    tc_file = tmp_path / "cases.yaml"
    tc_file.write_text(yaml.safe_dump([
        {"name": "只读查询", "precondition": "服务已启动", "steps": ["GET /health"],
         "observations": [{"check": "status", "expect": "200"}], "cleanup": "N/A"},
    ]))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "e2e_test_cases", "--file", str(tc_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["e2e_test_cases"][0]["cleanup"] == "N/A"


def test_feature_set_invalid_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "nonexistent_field", "value",
    ])
    assert result.exit_code == 4
    assert "deploy" in result.output


def test_feature_set_deploy(tmp_path, monkeypatch):
    """deploy 整列表替换：一条一行文本。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    deploy_file = tmp_path / "deploy.yaml"
    deploy_file.write_text(yaml.safe_dump([
        "prod 的 config.yaml 把 retry 从 3 改成 5，改完重启服务确认生效",
        "把 sqlite 旧表数据迁到新 schema，迁完核对行数一致",
    ], allow_unicode=True))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "deploy", "--file", str(deploy_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert len(feat["deploy"]) == 2
    assert "retry 从 3 改成 5" in feat["deploy"][0]


def test_feature_set_deploy_accepts_empty_list(tmp_path, monkeypatch):
    """无上线变更时写 []，表示已确认无需执行。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    deploy_file = tmp_path / "deploy.yaml"
    deploy_file.write_text("[]\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "deploy", "--file", str(deploy_file),
    ])
    assert result.exit_code == 0, result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat["deploy"] == []


def test_feature_set_deploy_rejects_blank_item(tmp_path, monkeypatch):
    """空条目拒绝写入，避免占位式清单。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    deploy_file = tmp_path / "deploy.yaml"
    deploy_file.write_text(yaml.safe_dump(["改配置", "  "], allow_unicode=True))

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "deploy", "--file", str(deploy_file),
    ])
    assert result.exit_code == 1
    assert "deploy[2]" in result.output

    feat = load_yaml(tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml")
    assert feat.get("deploy") in (None, [])


def test_feature_set_deploy_requires_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "set", "1", "deploy", "改配置"])
    assert result.exit_code == 4
    assert "--file" in result.output


def test_feature_set_spec_field_level_rejected(tmp_path, monkeypatch):
    """Field-level spec paths like spec.income.functions are NOT supported."""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    f = tmp_path / "x.yaml"
    f.write_text("x")
    result = runner.invoke(main, [
        "feature", "set", "1", "spec.income.functions", "--file", str(f),
    ])
    assert result.exit_code == 4


def test_feature_set_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "999", "user_input", "X",
    ])
    assert result.exit_code == 2


def test_feature_set_title_rejected(tmp_path, monkeypatch):
    """title is immutable (equals directory name)."""
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "title", "新标题",
    ])
    assert result.exit_code == 4  # title not a valid field


def _setup_feature(tmp_path):
    """Helper: create .features/001-test-feature/FEATURE.yaml + index.yaml entry."""
    (tmp_path / ".features" / "001-test-feature").mkdir(parents=True)
    (tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml").write_text(
        "id: 1\ntitle: '001-test-feature'\ndesc: test input\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: '001-test-feature'\n    status: draft\n    priority: P2\n"
    )


def _setup_feature_with_spec(tmp_path):
    """Helper: create feature with spec.income already present."""
    _setup_feature(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["spec"] = {
        "income": {"functions": ["录入"]}
    }
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))


def test_feature_show_markdown_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0
    assert "001-test-feature" in result.output
    assert "test input" in result.output


def test_feature_show_renders_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["summary"] = "解决看不到净收支的问题，新增收入模块"
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0, result.output
    assert "**Summary**: 解决看不到净收支的问题，新增收入模块" in result.output


def test_feature_show_renders_new_structure(tmp_path, monkeypatch):
    """Verify markdown show renders background, spec, e2e_test_cases."""
    monkeypatch.chdir(tmp_path)
    _setup_feature_with_full_data(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0
    assert "## Background" in result.output
    assert "痛点" in result.output
    assert "收益" in result.output
    assert "## Spec — income" in result.output
    assert "## E2E Test Cases" in result.output
    assert "t1" in result.output
    assert "observations" in result.output


def test_feature_show_yaml_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "yaml"])
    assert result.exit_code == 0
    assert "id: 1" in result.output
    assert "001-test-feature" in result.output


def test_feature_show_json_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["id"] == 1
    assert data["title"] == "001-test-feature"


def test_feature_show_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "999"])
    assert result.exit_code == 2


def test_feature_list_default_table(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list"])
    assert result.exit_code == 0
    assert "1" in result.output
    assert "001-test-feature" in result.output


def test_feature_list_table_includes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["summary"] = "解决看不到净收支的问题"
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list"])
    assert result.exit_code == 0, result.output
    assert "解决看不到净收支的问题" in result.output


def test_feature_list_json_includes_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["summary"] = "解决看不到净收支的问题"
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list", "--format", "json"])
    assert result.exit_code == 0, result.output
    import json
    rows = json.loads(result.output)
    assert rows[0]["summary"] == "解决看不到净收支的问题"


def test_feature_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Setup 2 features: one draft, one done
    _setup_minimal_feature(tmp_path, 1, "001-a", "desc1")
    _setup_minimal_feature(tmp_path, 2, "002-b", "desc2")
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n"
        "  - id: 1\n    title: '001-a'\n    status: draft\n    priority: P2\n"
        "  - id: 2\n    title: '002-b'\n    status: done\n    priority: P1\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list", "--status", "done"])
    assert result.exit_code == 0
    assert "002-b" in result.output
    assert "001-a\n" not in result.output  # filtered out (full line)


def test_feature_transition_draft_to_designing_requires_background(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)  # no background → should fail

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 1  # validation failure (background empty)

    # Now set background
    runner.invoke(main, ["feature", "set", "1", "background.pain_point", "痛点"])
    runner.invoke(main, ["feature", "set", "1", "background.benefit", "收益"])
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 0, result.output
    assert "draft → designing" in result.output

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "designing"


def test_feature_transition_designing_to_approved_requires_spec_only(tmp_path, monkeypatch):
    """designing → approved 只要求 spec；e2e_test_cases 可为空（无 E2E 场景的需求）。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature_with_background(tmp_path)
    # Transition to designing first
    runner = CliRunner()
    runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])

    # Try transition to approved without spec → fail
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 1  # missing spec

    # Add spec module only (no e2e_test_cases)
    spec_file = tmp_path / "m.yaml"
    spec_file.write_text(yaml.safe_dump({"functions": ["录入"]}))
    runner.invoke(main, ["feature", "set", "1", "spec.income", "--file", str(spec_file)])

    # e2e_test_cases 为空也应能进入 approved
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 0, result.output
    assert "designing → approved" in result.output


def test_feature_transition_designing_to_approved_requires_cleanup(tmp_path, monkeypatch):
    """非空 e2e_test_cases 中每条用例必须声明非空 cleanup 才能进入 approved。"""
    monkeypatch.chdir(tmp_path)
    _setup_feature_with_background(tmp_path)
    runner = CliRunner()
    runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])

    spec_file = tmp_path / "m.yaml"
    spec_file.write_text(yaml.safe_dump({"functions": ["录入"]}))
    runner.invoke(main, ["feature", "set", "1", "spec.income", "--file", str(spec_file)])

    # 历史/手写数据：用例缺少 cleanup
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["e2e_test_cases"] = [{"name": "t1", "precondition": "p", "steps": ["s"]}]
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))

    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 1
    assert "cleanup 为空" in result.output

    data["e2e_test_cases"][0]["cleanup"] = ["rm -f /tmp/qa-t1"]
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))

    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 0, result.output


def test_feature_transition_approved_to_implementing_no_check(tmp_path, monkeypatch):
    """approved → implementing has no extra check (decisions removed)."""
    monkeypatch.chdir(tmp_path)
    _setup_feature_approved(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "implementing"])
    assert result.exit_code == 0, result.output
    assert "approved → implementing" in result.output


def test_feature_transition_invalid_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    # draft → done is invalid
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "done"])
    assert result.exit_code == 3  # invalid state path


def test_feature_delete_requires_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "1"])
    assert result.exit_code == 1  # --force required


def test_feature_delete_with_force(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "1", "--force"])
    assert result.exit_code == 0
    assert "Deleted feature 1" in result.output

    assert not (tmp_path / ".features" / "001-test-feature").exists()
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 0


def test_feature_delete_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "999", "--force"])
    assert result.exit_code == 2


# --- Helpers ---

def _setup_minimal_feature(tmp_path, fid, dir_name, user_input):
    """Create a minimal feature with given id, dir_name, user_input."""
    (tmp_path / ".features" / dir_name).mkdir(parents=True)
    (tmp_path / ".features" / dir_name / "FEATURE.yaml").write_text(
        f"id: {fid}\ntitle: '{dir_name}'\ndesc: {user_input}\n"
    )


def _setup_feature_with_background(tmp_path):
    """Create feature with background filled (ready for designing transition)."""
    _setup_feature(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["background"] = {"pain_point": "痛点", "benefit": "收益"}
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))


def _setup_feature_approved(tmp_path):
    """Create feature at approved status (skip validations for approved→implementing test)."""
    _setup_feature_with_spec_and_cases(tmp_path)
    idx_file = tmp_path / ".features" / "index.yaml"
    idx_file.write_text(
        "features:\n  - id: 1\n    title: '001-test-feature'\n    status: approved\n    priority: P2\n"
    )


def _setup_feature_with_spec_and_cases(tmp_path):
    """Create feature with spec + e2e_test_cases filled."""
    _setup_feature_with_background(tmp_path)
    feat_file = tmp_path / ".features" / "001-test-feature" / "FEATURE.yaml"
    data = load_yaml(feat_file)
    data["spec"] = {"income": {"functions": ["录入"]}}
    data["e2e_test_cases"] = [{"name": "t1", "precondition": "p", "inputs": {}, "steps": ["s"], "observations": [{"check": "obs", "expect": "e"}], "cleanup": ["rm -f /tmp/qa-t1"]}]
    feat_file.write_text(yaml.safe_dump(data, allow_unicode=True))


def _setup_feature_with_full_data(tmp_path):
    """Create feature with background + spec + e2e_test_cases for show test."""
    _setup_feature_with_spec_and_cases(tmp_path)


# --- 拆分（--parent）---

def _init_features(tmp_path):
    """初始化 .features/index.yaml（不需要 git 仓库）。"""
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")


def _inject_worktree_record(tmp_path, dir_name):
    """往 FEATURE.yaml 注入 worktree 记录。

    `feature new --parent` 只校验父的 worktree 记录是否存在，不碰 git；
    worktree 的真实创建由 test_cli_worktree.py 覆盖。
    """
    feat = tmp_path / ".features" / dir_name / "FEATURE.yaml"
    data = load_yaml(feat)
    data["worktree"] = {
        "name": f"feat-{dir_name}",
        "branch": f"feature/{dir_name}",
        "path": f".worktrees/feat-{dir_name}",
        "base": "origin/dev",
    }
    feat.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def _new_feature(runner, slug, parent=None):
    """Invoke `feature new` with the given slug; optional --parent."""
    args = ["feature", "new", "--title", slug, "--slug", slug, "--user-input", "d"]
    if parent is not None:
        args += ["--parent", str(parent)]
    return runner.invoke(main, args)


def test_feature_new_with_parent_writes_both_sides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "parent-req").exit_code == 0
    _inject_worktree_record(tmp_path, "001-parent-req")

    result = _new_feature(runner, "child-a", parent=1)
    assert result.exit_code == 0, result.output

    # 子侧：权威字段
    child = load_yaml(tmp_path / ".features" / "002-child-a" / "FEATURE.yaml")
    assert child["parent"] == 1
    assert child["children"] == []

    # 父侧：派生视图
    parent = load_yaml(tmp_path / ".features" / "001-parent-req" / "FEATURE.yaml")
    assert parent["children"] == [2]
    assert parent["parent"] is None


def test_feature_new_parent_without_worktree_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "parent-req").exit_code == 0

    result = _new_feature(runner, "child-a", parent=1)
    assert result.exit_code == 1
    assert "尚无 worktree" in result.output
    # fail fast：校验失败时不建目录
    assert not (tmp_path / ".features" / "002-child-a").exists()


def test_feature_new_parent_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()

    result = _new_feature(runner, "child-a", parent=99)
    assert result.exit_code == 2
    assert not (tmp_path / ".features" / "001-child-a").exists()


def test_feature_new_rejects_grandchild(tmp_path, monkeypatch):
    """只允许一级拆分：父自身是子 feature 时拒绝。"""
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "parent-req").exit_code == 0
    _inject_worktree_record(tmp_path, "001-parent-req")
    assert _new_feature(runner, "child-a", parent=1).exit_code == 0

    result = _new_feature(runner, "grand", parent=2)
    assert result.exit_code == 1
    assert "只允许一级拆分" in result.output


def test_feature_show_children_rollup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "parent-req").exit_code == 0
    _inject_worktree_record(tmp_path, "001-parent-req")
    assert _new_feature(runner, "child-a", parent=1).exit_code == 0

    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0, result.output
    assert "## Children" in result.output
    assert "002-child-a" in result.output
    assert "draft" in result.output


def test_feature_show_child_prints_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "parent-req").exit_code == 0
    _inject_worktree_record(tmp_path, "001-parent-req")
    assert _new_feature(runner, "child-a", parent=1).exit_code == 0

    result = runner.invoke(main, ["feature", "show", "2"])
    assert result.exit_code == 0, result.output
    assert "**Parent**: feature #1" in result.output


def test_feature_new_without_parent_is_unchanged(tmp_path, monkeypatch):
    """回归：普通 feature 的 parent / children 保持空。"""
    monkeypatch.chdir(tmp_path)
    _init_features(tmp_path)
    runner = CliRunner()
    assert _new_feature(runner, "solo").exit_code == 0

    data = load_yaml(tmp_path / ".features" / "001-solo" / "FEATURE.yaml")
    assert data["parent"] is None
    assert data["children"] == []
