# agent_factory/schema/tests/test_validate.py
import pytest
from click.testing import CliRunner

from agent_factory.schema.validate import (
    validate_feature, validate_issue, validate_feature_index,
    validate_issue_index, validate_blocked, main,
)


def test_validate_feature_valid(tmp_path):
    yaml_content = """
id: 1
title: 测试 feature
agent_type: cli-only
problem: 这是一个测试问题。
benefit: 这是测试收益。
description: 详细描述。
"""
    f = tmp_path / "REQUIREMENTS.yaml"
    f.write_text(yaml_content)
    result = validate_feature(f)
    assert result is None  # valid 返回 None


def test_validate_feature_invalid(tmp_path, capsys):
    yaml_content = """
id: 1
title: 测试
agent_type: unknown-type
problem: x
benefit: y
description: z
"""
    f = tmp_path / "REQUIREMENTS.yaml"
    f.write_text(yaml_content)
    with pytest.raises(SystemExit):
        validate_feature(f)
    captured = capsys.readouterr()
    assert "agent_type" in captured.out or "agent_type" in captured.err


def test_validate_issue_valid(tmp_path):
    yaml_content = """
id: 1
title: 测试 issue
scenario: 复现场景描述。
impact: 影响范围描述。
"""
    f = tmp_path / "ISSUE.yaml"
    f.write_text(yaml_content)
    result = validate_issue(f)
    assert result is None


def test_validate_blocked_valid(tmp_path):
    yaml_content = """
reason: 测试原因。
action: 测试行动。
"""
    f = tmp_path / "BLOCKED.yaml"
    f.write_text(yaml_content)
    result = validate_blocked(f)
    assert result is None


def test_main_with_directory(tmp_path):
    """main 命令扫描目录下所有 YAML 文件"""
    feature_dir = tmp_path / "1"
    feature_dir.mkdir()
    (feature_dir / "REQUIREMENTS.yaml").write_text("""
id: 1
title: x
agent_type: cli-only
problem: x
benefit: y
description: z
""")
    (tmp_path / "index.yaml").write_text("features: []")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0


def test_main_nonexistent_path():
    runner = CliRunner()
    result = runner.invoke(main, ["/nonexistent/path"])
    assert result.exit_code != 0
