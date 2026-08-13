# CLI Command Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 agent-factory 实现 17 个 CLI 命令，让 PM (agent) 通过 shell 操作 YAML 需求文档（feature / issue / index 三组）。

**Architecture:** 在 `agent_factory/cli/` 新建命令模块（click 框架），100% 复用现有 `agent_factory/schema/` pydantic 模型。每个写命令内部 load YAML → pydantic 校验 → 修改 → dump YAML。删除独立 validate CLI 入口（保留 utility 函数）。

**Tech Stack:** Python 3.9+ / pydantic v2 / pyyaml / click / pytest

**Spec:** `agent-factory/docs/2026-08-09-cli-command-set-design.md`

---

## File Structure

| 路径 | 职责 | 操作 |
|------|------|------|
| `agent_factory/cli/__init__.py` | Main entry（click group），dispatches to feature/issue/index | 创建 |
| `agent_factory/cli/common.py` | Shared utilities: yaml load/dump, error format, path resolution | 创建 |
| `agent_factory/cli/feature.py` | feature 命令组（8 命令） | 创建 |
| `agent_factory/cli/issue.py` | issue 命令组（7 命令） | 创建 |
| `agent_factory/cli/index.py` | index 命令组（2 命令） | 创建 |
| `agent_factory/schema/validate.py` | 删除 CLI 入口（main + click decorators），保留 utility 函数 | 修改 |
| `agent_factory/schema/tests/test_validate.py` | 删除（旧 CLI 测试） | 删除 |
| `agent_factory/schema/tests/test_cli_common.py` | cli.common 测试 | 创建 |
| `agent_factory/schema/tests/test_cli_feature.py` | feature 命令组测试 | 创建 |
| `agent_factory/schema/tests/test_cli_issue.py` | issue 命令组测试 | 创建 |
| `agent_factory/schema/tests/test_cli_index.py` | index 命令组测试 | 创建 |
| `pyproject.toml` | console_scripts: `agent-factory-validate` → `agent-factory` | 修改 |
| `agent-factory/agent-pm.md` | 教 PM 用 CLI 命令代替直接编辑 YAML | 修改 |

**Conventions**:
- 测试在 `agent_factory/schema/tests/`（保持现有结构）
- 每个 cli 模块对应一个 test 文件
- 所有命令通过 `agent-factory` 单一入口（`agent_factory.cli:main`）

---

## Task 1: cli/ 骨架 + common.py

**Files:**
- Create: `agent_factory/cli/__init__.py`
- Create: `agent_factory/cli/common.py`
- Test: `agent_factory/schema/tests/test_cli_common.py`

- [ ] **Step 1: 写测试**

```python
# agent_factory/schema/tests/test_cli_common.py
import pytest
from pathlib import Path
from agent_factory.cli.common import (
    load_yaml, dump_yaml, find_feature_dir, find_issue_dir,
    format_error, next_feature_id, next_issue_id
)
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import FeatureStatus, Priority


def test_load_yaml(tmp_path):
    f = tmp_path / "test.yaml"
    f.write_text("id: 1\nname: test\n")
    data = load_yaml(f)
    assert data == {"id": 1, "name": "test"}


def test_dump_yaml(tmp_path):
    f = tmp_path / "out.yaml"
    dump_yaml(f, {"id": 1, "name": "测试"})
    content = f.read_text()
    assert "id: 1" in content
    assert "name: 测试" in content  # Unicode preserved


def test_find_feature_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text("id: 1\n")
    p = find_feature_dir(1)
    assert p.exists()
    assert p.name == "1"


def test_find_feature_dir_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        find_feature_dir(999)


def test_find_issue_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues" / "1").mkdir(parents=True)
    (tmp_path / ".issues" / "1" / "ISSUE.yaml").write_text("id: 1\n")
    p = find_issue_dir(1)
    assert p.exists()


def test_format_error():
    msg = format_error("ValidationError", "field X missing", ".features/1/REQUIREMENTS.yaml")
    assert "ValidationError" in msg
    assert "field X missing" in msg
    assert ".features/1/REQUIREMENTS.yaml" in msg


def test_next_feature_id_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    dump_yaml(tmp_path / ".features" / "index.yaml", {"features": []})
    assert next_feature_id() == 1


def test_next_feature_id_with_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    idx = FeatureIndex(features=[
        FeatureIndexItem(id=1, title="A", status=FeatureStatus.DRAFT, priority=Priority.P1),
        FeatureIndexItem(id=3, title="B", status=FeatureStatus.DONE, priority=Priority.P2),
    ])
    dump_yaml(tmp_path / ".features" / "index.yaml", idx.model_dump())
    assert next_feature_id() == 4


def test_next_issue_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    dump_yaml(tmp_path / ".issues" / "index.yaml", {"issues": []})
    assert next_issue_id() == 1
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_common.py -v
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 cli/common.py**

```python
# agent_factory/cli/common.py
"""Shared utilities for CLI commands."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel

from agent_factory.schema import FeatureIndex, IssueIndex


def load_yaml(path: Path) -> dict:
    """Load YAML file as dict."""
    with path.open() as f:
        return yaml.safe_load(f) or {}


def dump_yaml(path: Path, data: Any) -> None:
    """Dump data to YAML file (Unicode preserved, sort_keys=False)."""
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
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
```

- [ ] **Step 4: 写 cli/__init__.py（main entry placeholder）**

```python
# agent_factory/cli/__init__.py
"""agent-factory CLI main entry."""
from __future__ import annotations

import click


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


# Subcommand groups will be registered here as they are implemented:
# from agent_factory.cli import feature, issue, index
# main.add_command(feature.feature_group)
# main.add_command(issue.issue_group)
# main.add_command(index.index_group)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_common.py -v
```

Expected: 9 passed

- [ ] **Step 6: Commit**

```bash
git add agent_factory/cli/__init__.py agent_factory/cli/common.py agent_factory/schema/tests/test_cli_common.py
git commit -m "feat(cli): scaffold cli/ directory with common utilities"
```

---

## Task 2: 改造 validate.py（删除 CLI 入口）

**Files:**
- Modify: `agent_factory/schema/validate.py`
- Delete: `agent_factory/schema/tests/test_validate.py`

- [ ] **Step 1: 备份当前 validate.py 内容**

```bash
cat agent_factory/schema/validate.py
```

记录当前内容（含 main click 命令 + 6 个 validate_X 函数 + _validate_by_filename + _load_yaml + _format_error）。

- [ ] **Step 2: 重写 validate.py（只保留 utility 函数）**

```python
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
        loc = ".".join(str(x) for x in err["loc"])
        lines.append(f"  {loc}: {err['msg']}")
    return "\n".join(lines)
```

- [ ] **Step 3: 删除 test_validate.py**

```bash
rm agent_factory/schema/tests/test_validate.py
```

- [ ] **Step 4: 跑全部测试**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/ -v
```

Expected: 全部现有测试通过（除 test_validate.py 已删除），test_cli_common.py 9 passed。约 45+ tests。

- [ ] **Step 5: Commit**

```bash
git add agent_factory/schema/validate.py
git rm agent_factory/schema/tests/test_validate.py
git commit -m "refactor(schema): remove standalone validate CLI, keep utility functions"
```

---

## Task 3: feature new 命令

**Files:**
- Modify: `agent_factory/cli/feature.py` (create new file)
- Modify: `agent_factory/cli/__init__.py` (register feature group)
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 写测试**

```python
# agent_factory/schema/tests/test_cli_feature.py
import pytest
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
        "--agent-type", "cli-only",
        "--priority", "P1",
    ])
    assert result.exit_code == 0, result.output
    assert "Created feature 1" in result.output

    # REQS.yaml created
    reqs = tmp_path / ".features" / "1" / "REQUIREMENTS.yaml"
    assert reqs.exists()
    data = load_yaml(reqs)
    assert data["id"] == 1
    assert data["title"] == "收入管理"
    assert data["agent_type"] == "cli-only"

    # Index updated
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 1
    assert idx["features"][0]["id"] == 1
    assert idx["features"][0]["title"] == "收入管理"
    assert idx["features"][0]["status"] == "draft"
    assert idx["features"][0]["priority"] == "P1"


def test_feature_new_default_agent_type_and_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "X"])
    assert result.exit_code == 0

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["agent_type"] == "cli-only"  # default
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P2"  # default


def test_feature_new_invalid_agent_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "new", "--title", "X", "--agent-type", "unknown-type",
    ])
    assert result.exit_code == 1  # validation failure


def test_feature_new_increments_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "new", "--title", "B"])
    assert result.exit_code == 0
    assert "Created feature 2" in result.output
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: FAIL（feature 子命令不存在）

- [ ] **Step 3: 写 cli/feature.py（new 命令）**

```python
# agent_factory/cli/feature.py
"""feature command group."""
from __future__ import annotations

import sys
from pathlib import Path

import click
from pydantic import ValidationError

from agent_factory.cli.common import (
    dump_yaml, find_feature_dir, format_error, load_yaml, next_feature_id,
)
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import AgentType, FeatureStatus, Priority


@click.group()
def feature_group() -> None:
    """Operate feature REQUIREMENTS.yaml."""


@feature_group.command("new")
@click.option("--title", required=True, help="Feature title")
@click.option(
    "--agent-type",
    type=click.Choice([t.value for t in AgentType]),
    default=AgentType.CLI_ONLY.value,
    help="Agent type (default: cli-only)",
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in Priority]),
    default=Priority.P2.value,
    help="Priority (default: P2)",
)
def new(title: str, agent_type: str, priority: str) -> None:
    """Create new feature (status=draft)."""
    feature_id = next_feature_id()
    feature_dir = Path(".features") / str(feature_id)
    if feature_dir.exists():
        click.echo(format_error("FileExists", f"Feature {feature_id} already exists", str(feature_dir)), err=True)
        sys.exit(1)

    # Build Feature object (validates immediately)
    try:
        feature = Feature(
            id=feature_id,
            title=title,
            agent_type=AgentType(agent_type),
            problem="",  # placeholder, filled via `set` later
            benefit="",
            description="",
        )
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), None), err=True)
        sys.exit(1)

    # Create directory + REQS.yaml
    feature_dir.mkdir(parents=True)
    reqs_path = feature_dir / "REQUIREMENTS.yaml"
    dump_yaml(reqs_path, feature)

    # Update index.yaml
    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path)) if idx_path.exists() else FeatureIndex()
    idx.features.append(FeatureIndexItem(
        id=feature_id,
        title=title,
        status=FeatureStatus.DRAFT,
        priority=Priority(priority),
    ))
    dump_yaml(idx_path, idx)

    click.echo(f"Created feature {feature_id}: {title}")


# Other feature commands will be added in subsequent tasks:
# set / show / list / transition / block / unblock / delete
```

- [ ] **Step 4: 注册 feature_group 到 main**

修改 `agent_factory/cli/__init__.py`：

```python
# agent_factory/cli/__init__.py
"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


main.add_command(feature_group)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/cli/__init__.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature new' command"
```

---

## Task 4: feature set 命令（含 title 同步）

**Files:**
- Modify: `agent_factory/cli/feature.py`
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 追加测试到 test_cli_feature.py**

```python
# Append to agent_factory/schema/tests/test_cli_feature.py

def test_feature_set_simple_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "problem", "新问题描述",
    ])
    assert result.exit_code == 0, result.output
    assert "Updated feature 1: problem" in result.output

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["problem"] == "新问题描述"


def test_feature_set_long_field_from_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    # Write long content to temp file
    long_content = "这是详细描述\n含多行\n第三行"
    desc_file = tmp_path / "desc.md"
    desc_file.write_text(long_content)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "description", "--file", str(desc_file),
    ])
    assert result.exit_code == 0, result.output

    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["description"] == long_content


def test_feature_set_title_syncs_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "title", "新标题",
    ])
    assert result.exit_code == 0

    # REQS updated
    reqs = load_yaml(tmp_path / ".features" / "1" / "REQUIREMENTS.yaml")
    assert reqs["title"] == "新标题"
    # Index also updated (sync)
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["title"] == "新标题"


def test_feature_set_invalid_field_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "1", "nonexistent_field", "value",
    ])
    assert result.exit_code != 0


def test_feature_set_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "set", "999", "problem", "X",
    ])
    assert result.exit_code == 2


def _setup_feature(tmp_path):
    """Helper: create .features/1/REQUIREMENTS.yaml + index.yaml entry."""
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: 测试\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: 测试\n    status: draft\n    priority: P2\n"
    )
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py::test_feature_set_simple_field -v
```

Expected: FAIL（set 命令不存在）

- [ ] **Step 3: 在 cli/feature.py 追加 set 命令**

```python
# Append to agent_factory/cli/feature.py

# Fields that route to REQS.yaml
REQS_FIELDS = {
    "title", "agent_type", "problem", "benefit", "description",
    "data_schema", "interfaces", "acceptance_cases", "decisions",
}


@feature_group.command("set")
@click.argument("feature_id", type=int)
@click.argument("field")
@click.argument("value", required=False)
@click.option("--file", "file_path", type=click.Path(exists=True, path_type=Path), help="Read value from file")
def set_field(feature_id: int, field: str, value: str | None, file_path: Path | None) -> None:
    """Update a field in REQUIREMENTS.yaml.

    For 'title', also syncs to index.yaml.
    For long fields (description / data_schema / interfaces / acceptance_cases / decisions),
    use --file to read from a file.
    """
    if field not in REQS_FIELDS:
        click.echo(format_error("InvalidField", f"Field '{field}' not supported. Valid: {sorted(REQS_FIELDS)}", None), err=True)
        sys.exit(4)

    if file_path:
        new_value = file_path.read_text()
    elif value is not None:
        new_value = value
    else:
        click.echo(format_error("MissingValue", "Either VALUE or --file required", None), err=True)
        sys.exit(4)

    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    reqs_path = feature_dir / "REQUIREMENTS.yaml"
    try:
        data = load_yaml(reqs_path)
        data[field] = new_value
        feature = Feature.model_validate(data)  # validates
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(reqs_path)), err=True)
        sys.exit(1)

    dump_yaml(reqs_path, feature)

    # Sync title to index
    if field == "title":
        idx_path = Path(".features") / "index.yaml"
        idx = FeatureIndex.model_validate(load_yaml(idx_path))
        for item in idx.features:
            if item.id == feature_id:
                item.title = new_value
                break
        dump_yaml(idx_path, idx)

    click.echo(f"Updated feature {feature_id}: {field}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 10 passed (4 from Task 3 + 6 new)

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature set' command with title sync to index"
```

---

## Task 5: feature show / list 命令

**Files:**
- Modify: `agent_factory/cli/feature.py`
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 追加测试**

```python
# Append to test_cli_feature.py

def test_feature_show_markdown_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1"])
    assert result.exit_code == 0
    assert "# Feature 1: 测试" in result.output or "Feature 1" in result.output
    assert "测试" in result.output


def test_feature_show_yaml_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "yaml"])
    assert result.exit_code == 0
    assert "id: 1" in result.output
    assert "title: 测试" in result.output


def test_feature_show_json_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "show", "1", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["id"] == 1
    assert data["title"] == "测试"


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
    assert "测试" in result.output


def test_feature_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Setup 2 features: one draft, one done
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text("id: 1\ntitle: A\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n")
    (tmp_path / ".features" / "2").mkdir(parents=True)
    (tmp_path / ".features" / "2" / "REQUIREMENTS.yaml").write_text("id: 2\ntitle: B\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n")
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n"
        "  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
        "  - id: 2\n    title: B\n    status: done\n    priority: P1\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "list", "--status", "done"])
    assert result.exit_code == 0
    assert "B" in result.output
    assert "A" not in result.output  # filtered out
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py::test_feature_show_markdown_default -v
```

Expected: FAIL

- [ ] **Step 3: 追加 show + list 命令到 cli/feature.py**

```python
# Append to agent_factory/cli/feature.py

import json


@feature_group.command("show")
@click.argument("feature_id", type=int)
@click.option("--format", "fmt", type=click.Choice(["markdown", "yaml", "json"]), default="markdown")
def show(feature_id: int, fmt: str) -> None:
    """Show feature details."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    reqs_path = feature_dir / "REQUIREMENTS.yaml"
    data = load_yaml(reqs_path)
    feature = Feature.model_validate(data)

    if fmt == "json":
        click.echo(json.dumps(feature.model_dump(mode="json"), ensure_ascii=False, indent=2))
    elif fmt == "yaml":
        click.echo(yaml.safe_dump(feature.model_dump(mode="json"), allow_unicode=True, sort_keys=False))
    else:  # markdown
        click.echo(_render_feature_markdown(feature))


def _render_feature_markdown(feature: Feature) -> str:
    lines = [
        f"# Feature {feature.id}: {feature.title}",
        "",
        f"**Agent Type**: {feature.agent_type.value}",
        "",
        "## Problem",
        feature.problem,
        "",
        "## Benefit",
        feature.benefit,
        "",
        "## Description",
        feature.description,
        "",
    ]
    if feature.data_schema:
        lines += ["## Data Schema", "```python", feature.data_schema, "```", ""]
    if feature.interfaces:
        lines += ["## Interfaces", feature.interfaces, ""]
    if feature.acceptance_cases:
        lines += ["## Acceptance Cases", feature.acceptance_cases, ""]
    if feature.decisions:
        lines += ["## Decisions", ""]
        for dec in feature.decisions:
            lines += [f"### {dec.id}: {dec.question}", f"**Status**: {dec.status.value}", ""]
            for opt in dec.options:
                lines += [f"- **{opt.id}**: {opt.name} (pros: {opt.pros}; cons: {opt.cons})"]
            lines += [f"**Recommendation**: {dec.recommendation}", f"**Rationale**: {dec.rationale}", ""]
    return "\n".join(lines)


@feature_group.command("list")
@click.option("--status", type=click.Choice([s.value for s in FeatureStatus]), help="Filter by status")
@click.option("--priority", type=click.Choice([p.value for p in Priority]), help="Filter by priority")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_features(status: str | None, priority: str | None, fmt: str) -> None:
    """List features."""
    idx_path = Path(".features") / "index.yaml"
    if not idx_path.exists():
        click.echo("No features found.")
        return

    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    items = idx.features
    if status:
        items = [i for i in items if i.status.value == status]
    if priority:
        items = [i for i in items if i.priority.value == priority]

    if fmt == "json":
        click.echo(json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'ID':<5} {'STATUS':<15} {'PRIORITY':<10} TITLE")
        for item in items:
            click.echo(f"{item.id:<5} {item.status.value:<15} {item.priority.value:<10} {item.title}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 16 passed (10 from Task 3+4 + 6 new)

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature show' and 'feature list' commands"
```

---

## Task 6: feature transition 命令（状态机校验）

**Files:**
- Modify: `agent_factory/cli/feature.py`
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 追加测试**

```python
# Append to test_cli_feature.py

def test_feature_transition_draft_to_designing_requires_description(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)  # description is "z" (non-empty)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 0
    assert "draft → designing" in result.output

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "designing"


def test_feature_transition_blocked_when_description_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # Set description to empty
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: 测试\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: ''\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])
    assert result.exit_code == 1  # validation failure
    # Status unchanged
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "draft"


def test_feature_transition_designing_to_approved_requires_all_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # First transition to designing
    runner = CliRunner()
    runner.invoke(main, ["feature", "transition", "1", "--to", "designing"])

    # Try transition to approved without data_schema etc.
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "approved"])
    assert result.exit_code == 1  # missing data_schema / interfaces / acceptance_cases


def test_feature_transition_invalid_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    # draft → done is invalid (must go through designing, approved, implementing, qa-reviewing)
    result = runner.invoke(main, ["feature", "transition", "1", "--to", "done"])
    assert result.exit_code == 3  # invalid state path
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py::test_feature_transition_draft_to_designing_requires_description -v
```

Expected: FAIL

- [ ] **Step 3: 追加 transition 命令到 cli/feature.py**

```python
# Append to agent_factory/cli/feature.py

# State machine: allowed transitions
ALLOWED_TRANSITIONS = {
    FeatureStatus.DRAFT: {FeatureStatus.DESIGNING, FeatureStatus.CANCELLED},
    FeatureStatus.DESIGNING: {FeatureStatus.APPROVED, FeatureStatus.BLOCKED, FeatureStatus.CANCELLED},
    FeatureStatus.APPROVED: {FeatureStatus.IMPLEMENTING, FeatureStatus.CANCELLED},
    FeatureStatus.IMPLEMENTING: {FeatureStatus.QA_REVIEWING, FeatureStatus.BLOCKED},
    FeatureStatus.QA_REVIEWING: {FeatureStatus.DONE, FeatureStatus.IMPLEMENTING},  # QA fail 回 implementing
    FeatureStatus.BLOCKED: set(),  # 需 unblock 命令恢复
    FeatureStatus.DONE: set(),
    FeatureStatus.CANCELLED: set(),
}


def _validate_transition_requirements(current: FeatureStatus, target: FeatureStatus, feature: Feature) -> list[str]:
    """Return list of missing requirements for transition (empty = OK)."""
    issues = []
    if current == FeatureStatus.DRAFT and target == FeatureStatus.DESIGNING:
        if not feature.description.strip():
            issues.append("description is empty")
    elif current == FeatureStatus.DESIGNING and target == FeatureStatus.APPROVED:
        if not (feature.data_schema or "").strip():
            issues.append("data_schema is empty")
        if not (feature.interfaces or "").strip():
            issues.append("interfaces is empty")
        if not feature.acceptance_cases.strip():
            issues.append("acceptance_cases is empty")
    elif current == FeatureStatus.APPROVED and target == FeatureStatus.IMPLEMENTING:
        from agent_factory.schema.enums import DecisionStatus
        open_decisions = [d.id for d in feature.decisions if d.status != DecisionStatus.CLOSED]
        if open_decisions:
            issues.append(f"open decisions not closed: {open_decisions}")
    return issues


@feature_group.command("transition")
@click.argument("feature_id", type=int)
@click.option("--to", "target", required=True, type=click.Choice([s.value for s in FeatureStatus]))
def transition(feature_id: int, target: str) -> None:
    """Transition feature status (with cross-field validation)."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    target_status = FeatureStatus(target)

    # Load current status from index
    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    current_item = next((i for i in idx.features if i.id == feature_id), None)
    if not current_item:
        click.echo(format_error("NotFound", f"Feature {feature_id} not in index", None), err=True)
        sys.exit(2)

    current_status = current_item.status

    # Validate path
    if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        click.echo(format_error(
            "InvalidTransition",
            f"Path '{current_status.value} → {target_status.value}' is not allowed",
            None,
        ), err=True)
        sys.exit(3)

    # Cross-field validation (load REQS)
    reqs_path = feature_dir / "REQUIREMENTS.yaml"
    feature = Feature.model_validate(load_yaml(reqs_path))
    issues = _validate_transition_requirements(current_status, target_status, feature)
    if issues:
        click.echo(format_error(
            "ValidationError",
            f"Cannot transition to {target_status.value}: " + "; ".join(issues),
            str(reqs_path),
        ), err=True)
        sys.exit(1)

    # Update index
    current_item.status = target_status
    dump_yaml(idx_path, idx)

    click.echo(f"Transitioned feature {feature_id}: {current_status.value} → {target_status.value}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 20 passed (16 from Task 3+4+5 + 4 new)

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature transition' with state machine validation"
```

---

## Task 7: feature block / unblock 命令

**Files:**
- Modify: `agent_factory/cli/feature.py`
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 追加测试**

```python
# Append to test_cli_feature.py

def test_feature_block_creates_blocked_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "feature", "block", "1",
        "--reason", "卡住了",
        "--action", "等用户决策",
    ])
    assert result.exit_code == 0
    assert "Blocked feature 1" in result.output

    blocked = tmp_path / ".features" / "1" / "BLOCKED.yaml"
    assert blocked.exists()
    data = load_yaml(blocked)
    assert data["reason"] == "卡住了"
    assert data["action"] == "等用户决策"

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "blocked"


def test_feature_block_already_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    runner.invoke(main, ["feature", "block", "1", "--reason", "X", "--action", "Y"])
    result = runner.invoke(main, ["feature", "block", "1", "--reason", "X2", "--action", "Y2"])
    assert result.exit_code == 1  # already blocked


def test_feature_unblock_removes_blocked_yaml_and_restores_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)
    # Block first
    runner = CliRunner()
    runner.invoke(main, ["feature", "block", "1", "--reason", "X", "--action", "Y"])

    # Now unblock to designing
    result = runner.invoke(main, ["feature", "unblock", "1", "--to", "designing"])
    assert result.exit_code == 0
    assert "Unblocked feature 1" in result.output

    assert not (tmp_path / ".features" / "1" / "BLOCKED.yaml").exists()
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "designing"


def test_feature_unblock_not_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "unblock", "1", "--to", "designing"])
    assert result.exit_code == 1  # not blocked
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py::test_feature_block_creates_blocked_yaml -v
```

Expected: FAIL

- [ ] **Step 3: 追加 block + unblock 命令到 cli/feature.py**

```python
# Append to agent_factory/cli/feature.py

from agent_factory.schema import BlockedRecord


@feature_group.command("block")
@click.argument("feature_id", type=int)
@click.option("--reason", required=True, help="Why blocked")
@click.option("--action", required=True, help="What's needed to unblock")
def block(feature_id: int, reason: str, action: str) -> None:
    """Block feature (creates BLOCKED.yaml + sets status=blocked)."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    blocked_path = feature_dir / "BLOCKED.yaml"
    if blocked_path.exists():
        click.echo(format_error("AlreadyBlocked", f"Feature {feature_id} already blocked", str(blocked_path)), err=True)
        sys.exit(1)

    # Create BLOCKED.yaml
    record = BlockedRecord(reason=reason, action=action)
    dump_yaml(blocked_path, record)

    # Update index status
    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    item = next((i for i in idx.features if i.id == feature_id), None)
    if item:
        item.status = FeatureStatus.BLOCKED
        dump_yaml(idx_path, idx)

    click.echo(f"Blocked feature {feature_id}: {reason[:50]}")


@feature_group.command("unblock")
@click.argument("feature_id", type=int)
@click.option("--to", "target", required=True, type=click.Choice([s.value for s in FeatureStatus]))
def unblock(feature_id: int, target: str) -> None:
    """Unblock feature (removes BLOCKED.yaml + restores status to --to)."""
    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    blocked_path = feature_dir / "BLOCKED.yaml"
    if not blocked_path.exists():
        click.echo(format_error("NotBlocked", f"Feature {feature_id} is not blocked", None), err=True)
        sys.exit(1)

    target_status = FeatureStatus(target)
    # Validate path (blocked → target)
    if target_status not in {FeatureStatus.DESIGNING, FeatureStatus.IMPLEMENTING,
                             FeatureStatus.QA_REVIEWING, FeatureStatus.APPROVED,
                             FeatureStatus.CANCELLED}:
        click.echo(format_error("InvalidTransition", f"Cannot unblock to {target}", None), err=True)
        sys.exit(3)

    blocked_path.unlink()

    idx_path = Path(".features") / "index.yaml"
    idx = FeatureIndex.model_validate(load_yaml(idx_path))
    item = next((i for i in idx.features if i.id == feature_id), None)
    if item:
        item.status = target_status
        dump_yaml(idx_path, idx)

    click.echo(f"Unblocked feature {feature_id}: status → {target}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 24 passed (20 from previous + 4 new)

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature block' and 'feature unblock' commands"
```

---

## Task 8: feature delete 命令

**Files:**
- Modify: `agent_factory/cli/feature.py`
- Test: `agent_factory/schema/tests/test_cli_feature.py`

- [ ] **Step 1: 追加测试**

```python
# Append to test_cli_feature.py

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

    assert not (tmp_path / ".features" / "1").exists()
    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 0


def test_feature_delete_unknown_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_feature(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["feature", "delete", "999", "--force"])
    assert result.exit_code == 2
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py::test_feature_delete_with_force -v
```

Expected: FAIL

- [ ] **Step 3: 追加 delete 命令到 cli/feature.py**

```python
# Append to agent_factory/cli/feature.py

import shutil


@feature_group.command("delete")
@click.argument("feature_id", type=int)
@click.option("--force", is_flag=True, help="Required to actually delete (no interactive confirm)")
def delete(feature_id: int, force: bool) -> None:
    """Delete feature (directory + index entry)."""
    if not force:
        click.echo(format_error("ForceRequired", "Pass --force to confirm deletion", None), err=True)
        sys.exit(1)

    try:
        feature_dir = find_feature_dir(feature_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    # Remove directory
    shutil.rmtree(feature_dir)

    # Remove from index
    idx_path = Path(".features") / "index.yaml"
    if idx_path.exists():
        idx = FeatureIndex.model_validate(load_yaml(idx_path))
        idx.features = [i for i in idx.features if i.id != feature_id]
        dump_yaml(idx_path, idx)

    click.echo(f"Deleted feature {feature_id}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_feature.py -v
```

Expected: 27 passed (24 from previous + 3 new). feature 命令组 8 个命令全部完成。

- [ ] **Step 5: Commit**

```bash
git add agent_factory/cli/feature.py agent_factory/schema/tests/test_cli_feature.py
git commit -m "feat(cli): add 'feature delete' command (--force required)"
```

---

## Task 9: issue 命令组（7 个命令）

**Files:**
- Create: `agent_factory/cli/issue.py`
- Modify: `agent_factory/cli/__init__.py` (register issue_group)
- Test: `agent_factory/schema/tests/test_cli_issue.py`

issue 命令组结构与 feature 对称（new / set / show / list / transition / block / unblock）。复用 feature.py 的模式。

- [ ] **Step 1: 写测试（覆盖 7 个命令的核心场景）**

```python
# agent_factory/schema/tests/test_cli_issue.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def _setup_issue(tmp_path):
    """Helper: create .issues/1/ISSUE.yaml + index.yaml entry."""
    (tmp_path / ".issues" / "1").mkdir(parents=True)
    (tmp_path / ".issues" / "1" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: 测试 bug\nscenario: 复现步骤\nimpact: 影响范围\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: 测试 bug\n    type: bug\n    status: open\n    priority: P2\n"
    )


def test_issue_new_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "new",
        "--title", "登录崩溃",
        "--type", "bug",
        "--priority", "P1",
    ])
    assert result.exit_code == 0
    assert "Created issue 1" in result.output

    issue = load_yaml(tmp_path / ".issues" / "1" / "ISSUE.yaml")
    assert issue["title"] == "登录崩溃"

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["type"] == "bug"
    assert idx["issues"][0]["priority"] == "P1"


def test_issue_set_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, [
        "issue", "set", "1", "root_cause", "代码 bug",
    ])
    assert result.exit_code == 0

    issue = load_yaml(tmp_path / ".issues" / "1" / "ISSUE.yaml")
    assert issue["root_cause"] == "代码 bug"


def test_issue_set_title_syncs_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "set", "1", "title", "新标题"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["title"] == "新标题"


def test_issue_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "show", "1"])
    assert result.exit_code == 0
    assert "测试 bug" in result.output


def test_issue_list_filter_by_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "list", "--type", "bug"])
    assert result.exit_code == 0
    assert "测试 bug" in result.output


def test_issue_transition_open_to_triaging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["issue", "transition", "1", "--to", "triaging"])
    assert result.exit_code == 0
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "triaging"


def test_issue_block_unblock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _setup_issue(tmp_path)

    runner = CliRunner()
    # Block
    result = runner.invoke(main, ["issue", "block", "1", "--reason", "X", "--action", "Y"])
    assert result.exit_code == 0
    assert (tmp_path / ".issues" / "1" / "BLOCKED.yaml").exists()

    # Unblock
    result = runner.invoke(main, ["issue", "unblock", "1", "--to", "triaging"])
    assert result.exit_code == 0
    assert not (tmp_path / ".issues" / "1" / "BLOCKED.yaml").exists()
    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["status"] == "triaging"
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_issue.py -v
```

Expected: FAIL（issue 子命令不存在）

- [ ] **Step 3: 写 cli/issue.py（7 个命令）**

```python
# agent_factory/cli/issue.py
"""issue command group. Mirrors feature command group structure."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from agent_factory.cli.common import (
    dump_yaml, find_issue_dir, format_error, load_yaml, next_issue_id,
)
from agent_factory.schema import BlockedRecord, Issue, IssueIndex, IssueIndexItem
from agent_factory.schema.enums import IssueStatus, IssueType, Priority


@click.group()
def issue_group() -> None:
    """Operate issue ISSUE.yaml."""


ISSUE_FIELDS = {
    "title", "scenario", "impact",
    "root_cause", "fix_suggestion", "fix", "resolution",
}


@issue_group.command("new")
@click.option("--title", required=True)
@click.option("--type", "issue_type", required=True,
              type=click.Choice([t.value for t in IssueType]))
@click.option("--priority", default=Priority.P2.value,
              type=click.Choice([p.value for p in Priority]))
def new(title: str, issue_type: str, priority: str) -> None:
    """Create new issue (status=open)."""
    issue_id = next_issue_id()
    issue_dir = Path(".issues") / str(issue_id)
    if issue_dir.exists():
        click.echo(format_error("FileExists", f"Issue {issue_id} already exists", str(issue_dir)), err=True)
        sys.exit(1)

    try:
        issue = Issue(
            id=issue_id,
            title=title,
            scenario="",
            impact="",
        )
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), None), err=True)
        sys.exit(1)

    issue_dir.mkdir(parents=True)
    dump_yaml(issue_dir / "ISSUE.yaml", issue)

    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path)) if idx_path.exists() else IssueIndex()
    idx.issues.append(IssueIndexItem(
        id=issue_id,
        title=title,
        type=IssueType(issue_type),
        status=IssueStatus.OPEN,
        priority=Priority(priority),
    ))
    dump_yaml(idx_path, idx)

    click.echo(f"Created issue {issue_id}: {title}")


@issue_group.command("set")
@click.argument("issue_id", type=int)
@click.argument("field")
@click.argument("value", required=False)
@click.option("--file", "file_path", type=click.Path(exists=True, path_type=Path))
def set_field(issue_id: int, field: str, value: str | None, file_path: Path | None) -> None:
    """Update a field in ISSUE.yaml. 'title' syncs to index."""
    if field not in ISSUE_FIELDS:
        click.echo(format_error("InvalidField", f"Field '{field}' not supported. Valid: {sorted(ISSUE_FIELDS)}", None), err=True)
        sys.exit(4)

    if file_path:
        new_value = file_path.read_text()
    elif value is not None:
        new_value = value
    else:
        click.echo(format_error("MissingValue", "Either VALUE or --file required", None), err=True)
        sys.exit(4)

    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    issue_path = issue_dir / "ISSUE.yaml"
    try:
        data = load_yaml(issue_path)
        data[field] = new_value
        issue = Issue.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(issue_path)), err=True)
        sys.exit(1)

    dump_yaml(issue_path, issue)

    if field == "title":
        idx_path = Path(".issues") / "index.yaml"
        idx = IssueIndex.model_validate(load_yaml(idx_path))
        for item in idx.issues:
            if item.id == issue_id:
                item.title = new_value
                break
        dump_yaml(idx_path, idx)

    click.echo(f"Updated issue {issue_id}: {field}")


@issue_group.command("show")
@click.argument("issue_id", type=int)
@click.option("--format", "fmt", type=click.Choice(["markdown", "yaml", "json"]), default="markdown")
def show(issue_id: int, fmt: str) -> None:
    """Show issue details."""
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    issue = Issue.model_validate(load_yaml(issue_dir / "ISSUE.yaml"))

    if fmt == "json":
        click.echo(json.dumps(issue.model_dump(mode="json"), ensure_ascii=False, indent=2))
    elif fmt == "yaml":
        click.echo(yaml.safe_dump(issue.model_dump(mode="json"), allow_unicode=True, sort_keys=False))
    else:
        click.echo(f"# Issue {issue.id}: {issue.title}\n")
        click.echo(f"## Scenario\n{issue.scenario}\n")
        click.echo(f"## Impact\n{issue.impact}\n")
        if issue.root_cause:
            click.echo(f"## Root Cause\n{issue.root_cause}\n")
        if issue.fix_suggestion:
            click.echo(f"## Fix Suggestion\n{issue.fix_suggestion}\n")
        if issue.fix:
            click.echo(f"## Fix\n{issue.fix}\n")
        if issue.resolution:
            click.echo(f"## Resolution\n{issue.resolution}\n")


@issue_group.command("list")
@click.option("--status", type=click.Choice([s.value for s in IssueStatus]))
@click.option("--type", "issue_type", type=click.Choice([t.value for t in IssueType]))
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_issues(status: str | None, issue_type: str | None, fmt: str) -> None:
    """List issues."""
    idx_path = Path(".issues") / "index.yaml"
    if not idx_path.exists():
        click.echo("No issues found.")
        return

    idx = IssueIndex.model_validate(load_yaml(idx_path))
    items = idx.issues
    if status:
        items = [i for i in items if i.status.value == status]
    if issue_type:
        items = [i for i in items if i.type.value == issue_type]

    if fmt == "json":
        click.echo(json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'ID':<5} {'TYPE':<18} {'STATUS':<10} {'PRIORITY':<10} TITLE")
        for item in items:
            click.echo(f"{item.id:<5} {item.type.value:<18} {item.status.value:<10} {item.priority.value:<10} {item.title}")


# Issue state machine: open → triaging → closed
ALLOWED_ISSUE_TRANSITIONS = {
    IssueStatus.OPEN: {IssueStatus.TRIAGING, IssueStatus.CLOSED},
    IssueStatus.TRIAGING: {IssueStatus.CLOSED, IssueStatus.OPEN},
    IssueStatus.CLOSED: set(),
}


@issue_group.command("transition")
@click.argument("issue_id", type=int)
@click.option("--to", "target", required=True, type=click.Choice([s.value for s in IssueStatus]))
def transition(issue_id: int, target: str) -> None:
    """Transition issue status."""
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    target_status = IssueStatus(target)

    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    current_item = next((i for i in idx.issues if i.id == issue_id), None)
    if not current_item:
        click.echo(format_error("NotFound", f"Issue {issue_id} not in index", None), err=True)
        sys.exit(2)

    current_status = current_item.status
    if target_status not in ALLOWED_ISSUE_TRANSITIONS.get(current_status, set()):
        click.echo(format_error(
            "InvalidTransition",
            f"Path '{current_status.value} → {target_status.value}' is not allowed",
            None,
        ), err=True)
        sys.exit(3)

    current_item.status = target_status
    dump_yaml(idx_path, idx)

    click.echo(f"Transitioned issue {issue_id}: {current_status.value} → {target_status.value}")


@issue_group.command("block")
@click.argument("issue_id", type=int)
@click.option("--reason", required=True)
@click.option("--action", "action_text", required=True)
def block(issue_id: int, reason: str, action_text: str) -> None:
    """Block issue."""
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    blocked_path = issue_dir / "BLOCKED.yaml"
    if blocked_path.exists():
        click.echo(format_error("AlreadyBlocked", f"Issue {issue_id} already blocked", str(blocked_path)), err=True)
        sys.exit(1)

    dump_yaml(blocked_path, BlockedRecord(reason=reason, action=action_text))

    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    for item in idx.issues:
        if item.id == issue_id:
            item.status = IssueStatus.TRIAGING  # issue 没有专门 blocked 状态，停留在 triaging
            break
    dump_yaml(idx_path, idx)

    click.echo(f"Blocked issue {issue_id}: {reason[:50]}")


@issue_group.command("unblock")
@click.argument("issue_id", type=int)
@click.option("--to", "target", required=True, type=click.Choice([s.value for s in IssueStatus]))
def unblock(issue_id: int, target: str) -> None:
    """Unblock issue."""
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    blocked_path = issue_dir / "BLOCKED.yaml"
    if not blocked_path.exists():
        click.echo(format_error("NotBlocked", f"Issue {issue_id} is not blocked", None), err=True)
        sys.exit(1)

    blocked_path.unlink()

    target_status = IssueStatus(target)
    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    for item in idx.issues:
        if item.id == issue_id:
            item.status = target_status
            break
    dump_yaml(idx_path, idx)

    click.echo(f"Unblocked issue {issue_id}: status → {target}")
```

- [ ] **Step 4: 注册 issue_group 到 main**

修改 `agent_factory/cli/__init__.py`：

```python
# agent_factory/cli/__init__.py
"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group
from agent_factory.cli.issue import issue_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


main.add_command(feature_group)
main.add_command(issue_group)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_issue.py -v
```

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add agent_factory/cli/issue.py agent_factory/cli/__init__.py agent_factory/schema/tests/test_cli_issue.py
git commit -m "feat(cli): add issue command group (new/set/show/list/transition/block/unblock)"
```

---

## Task 10: index 命令组（set / refresh）

**Files:**
- Create: `agent_factory/cli/index.py`
- Modify: `agent_factory/cli/__init__.py` (register index_group)
- Test: `agent_factory/schema/tests/test_cli_index.py`

- [ ] **Step 1: 写测试**

```python
# agent_factory/schema/tests/test_cli_index.py
import pytest
from click.testing import CliRunner

from agent_factory.cli import main
from agent_factory.cli.common import load_yaml


def test_index_set_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "priority", "P1"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["priority"] == "P1"


def test_index_set_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "status", "done"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert idx["features"][0]["status"] == "done"


def test_index_set_title_rejected(tmp_path, monkeypatch):
    """title must be set via feature/issue set, not index set."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".features").mkdir()
    (tmp_path / ".features" / "index.yaml").write_text(
        "features:\n  - id: 1\n    title: A\n    status: draft\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "feature", "1", "title", "新"])
    assert result.exit_code != 0  # rejected


def test_index_set_issue_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues").mkdir()
    (tmp_path / ".issues" / "index.yaml").write_text(
        "issues:\n  - id: 1\n    title: A\n    type: bug\n    status: open\n    priority: P2\n"
    )

    runner = CliRunner()
    result = runner.invoke(main, ["index", "set", "issue", "1", "type", "feature-request"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert idx["issues"][0]["type"] == "feature-request"


def test_index_refresh_rebuilds_feature_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create 2 features without proper index
    (tmp_path / ".features" / "1").mkdir(parents=True)
    (tmp_path / ".features" / "1" / "REQUIREMENTS.yaml").write_text(
        "id: 1\ntitle: A\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    (tmp_path / ".features" / "2").mkdir(parents=True)
    (tmp_path / ".features" / "2" / "REQUIREMENTS.yaml").write_text(
        "id: 2\ntitle: B\nagent_type: cli-only\nproblem: x\nbenefit: y\ndescription: z\n"
    )
    # Empty / corrupt index
    (tmp_path / ".features" / "index.yaml").write_text("features: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "feature"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".features" / "index.yaml")
    assert len(idx["features"]) == 2
    titles = [f["title"] for f in idx["features"]]
    assert "A" in titles
    assert "B" in titles


def test_index_refresh_issue_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".issues" / "1").mkdir(parents=True)
    (tmp_path / ".issues" / "1" / "ISSUE.yaml").write_text(
        "id: 1\ntitle: A\nscenario: x\nimpact: y\n"
    )
    (tmp_path / ".issues" / "index.yaml").write_text("issues: []\n")

    runner = CliRunner()
    result = runner.invoke(main, ["index", "refresh", "issue"])
    assert result.exit_code == 0

    idx = load_yaml(tmp_path / ".issues" / "index.yaml")
    assert len(idx["issues"]) == 1
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_index.py -v
```

Expected: FAIL

- [ ] **Step 3: 写 cli/index.py**

```python
# agent_factory/cli/index.py
"""index command group."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from agent_factory.cli.common import dump_yaml, format_error, load_yaml
from agent_factory.schema import FeatureIndex, FeatureIndexItem, IssueIndex, IssueIndexItem
from agent_factory.schema.enums import FeatureStatus, IssueStatus, IssueType, Priority


# Fields that index set can modify (title NOT included - sync via feature/issue set)
INDEX_FEATURE_FIELDS = {"priority", "status"}
INDEX_ISSUE_FIELDS = {"priority", "status", "type"}


@click.group()
def index_group() -> None:
    """Operate index.yaml files."""


@index_group.command("set")
@click.argument("resource", type=click.Choice(["feature", "issue"]))
@click.argument("item_id", type=int)
@click.argument("field")
@click.argument("value")
def set_field(resource: str, item_id: int, field: str, value: str) -> None:
    """Update an index field (priority / status / type for issue). title NOT allowed."""
    allowed = INDEX_FEATURE_FIELDS if resource == "feature" else INDEX_ISSUE_FIELDS
    if field not in allowed:
        click.echo(format_error(
            "InvalidField",
            f"Field '{field}' not allowed for index set. Use feature/issue set for title. Allowed: {sorted(allowed)}",
            None,
        ), err=True)
        sys.exit(4)

    idx_path = Path(f".{resource}s") / "index.yaml"  # .features/ or .issues/
    if not idx_path.exists():
        click.echo(format_error("NotFound", f"Index file missing: {idx_path}", None), err=True)
        sys.exit(2)

    if resource == "feature":
        idx = FeatureIndex.model_validate(load_yaml(idx_path))
        items = idx.features
    else:
        idx = IssueIndex.model_validate(load_yaml(idx_path))
        items = idx.issues

    item = next((i for i in items if i.id == item_id), None)
    if not item:
        click.echo(format_error("NotFound", f"{resource} {item_id} not in index", None), err=True)
        sys.exit(2)

    # Validate value type
    try:
        if field == "priority":
            item.priority = Priority(value)
        elif field == "status":
            if resource == "feature":
                item.status = FeatureStatus(value)
            else:
                item.status = IssueStatus(value)
        elif field == "type":
            item.type = IssueType(value)
    except ValueError as exc:
        click.echo(format_error("ValidationError", str(exc), None), err=True)
        sys.exit(1)

    dump_yaml(idx_path, idx)
    click.echo(f"Updated {resource} {item_id}: {field} = {value}")


@index_group.command("refresh")
@click.argument("resource", type=click.Choice(["feature", "issue"]))
def refresh(resource: str) -> None:
    """Scan all REQUIREMENTS/ISSUE files and rebuild index.yaml."""
    base_dir = Path(f".{resource}s")
    if not base_dir.exists():
        click.echo(format_error("NotFound", f"Directory missing: {base_dir}", None), err=True)
        sys.exit(2)

    if resource == "feature":
        items = []
        for subdir in sorted(base_dir.iterdir()):
            if not subdir.is_dir() or not subdir.name.isdigit():
                continue
            reqs_path = subdir / "REQUIREMENTS.yaml"
            if not reqs_path.exists():
                continue
            data = load_yaml(reqs_path)
            items.append(FeatureIndexItem(
                id=data["id"],
                title=data["title"],
                status=FeatureStatus.DRAFT,  # refresh 不能推断 status，默认 draft（PM 用 transition 修正）
                priority=Priority.P2,  # 同上，默认 P2
            ))
        dump_yaml(base_dir / "index.yaml", FeatureIndex(features=items))
        click.echo(f"Refreshed feature index: {len(items)} items")
    else:
        items = []
        for subdir in sorted(base_dir.iterdir()):
            if not subdir.is_dir() or not subdir.name.isdigit():
                continue
            issue_path = subdir / "ISSUE.yaml"
            if not issue_path.exists():
                continue
            data = load_yaml(issue_path)
            items.append(IssueIndexItem(
                id=data["id"],
                title=data["title"],
                type=IssueType.BUG,  # refresh 不能推断 type，默认 bug
                status=IssueStatus.OPEN,
                priority=Priority.P2,
            ))
        dump_yaml(base_dir / "index.yaml", IssueIndex(issues=items))
        click.echo(f"Refreshed issue index: {len(items)} items")
```

- [ ] **Step 4: 注册 index_group 到 main**

修改 `agent_factory/cli/__init__.py`：

```python
# agent_factory/cli/__init__.py
"""agent-factory CLI main entry."""
from __future__ import annotations

import click

from agent_factory.cli.feature import feature_group
from agent_factory.cli.issue import issue_group
from agent_factory.cli.index import index_group


@click.group()
def main() -> None:
    """agent-factory CLI - operate YAML workflow files."""


main.add_command(feature_group)
main.add_command(issue_group)
main.add_command(index_group)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 跑测试确认通过**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/test_cli_index.py -v
```

Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add agent_factory/cli/index.py agent_factory/cli/__init__.py agent_factory/schema/tests/test_cli_index.py
git commit -m "feat(cli): add index command group (set/refresh)"
```

---

## Task 11: 更新 pyproject.toml console_scripts

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 替换 console_scripts 入口**

修改 `system-prompt/agent-factory/pyproject.toml`：

```toml
[project.scripts]
agent-factory = "agent_factory.cli:main"
```

（删除原来的 `agent-factory-validate = "agent_factory.schema.validate:main"`）

- [ ] **Step 2: 重装包**

```bash
cd system-prompt/agent-factory && pip install -e . --quiet
```

- [ ] **Step 3: 验证新命令可用**

```bash
agent-factory --help
```

Expected: 输出含 `feature`、`issue`、`index` 三个子命令组

```bash
agent-factory feature --help
```

Expected: 输出含 `new`、`set`、`show`、`list`、`transition`、`block`、`unblock`、`delete` 8 个命令

- [ ] **Step 4: 验证旧命令不存在**

```bash
agent-factory-validate --help 2>&1 || echo "OK: command not found"
```

Expected: command not found

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat(cli): rename console_script from agent-factory-validate to agent-factory"
```

---

## Task 12: agent-pm.md 集成（教 PM 用 CLI）

**Files:**
- Modify: `agent-pm.md`

agent-pm.md 当前教 PM 直接编辑 YAML 文件。改为教 PM 用 CLI 命令。

- [ ] **Step 1: 找出"PM 编辑 YAML"相关章节**

```bash
grep -n "编辑.*yaml\|修改.*yaml\|写入.*yaml\|更新.*yaml" agent-pm.md
```

记录所有需要改的章节（预计：Feature 工作流 / Issue 工作流 / 跨环境 _incoming 流程 / 状态流转）。

- [ ] **Step 2: 在 agent-pm.md 开头加 CLI 命令速查表**

在 `## Identity` 章节后插入新章节：

```markdown
## CLI 命令速查

PM 通过 shell 调用 `agent-factory` CLI 操作 YAML 文件，不直接编辑 YAML。

### feature 命令组

| 命令 | 用途 |
|------|------|
| `agent-factory feature new --title "..." [--agent-type X --priority Y]` | 创建 feature |
| `agent-factory feature set <id> <field> [value | --file <path>]` | 更新字段（title 自动同步 index） |
| `agent-factory feature show <id> [--format markdown\|yaml\|json]` | 查看 |
| `agent-factory feature list [--status X --priority Y]` | 列出 |
| `agent-factory feature transition <id> --to <status>` | 状态流转（含跨字段校验） |
| `agent-factory feature block <id> --reason "..." --action "..."` | 阻塞 |
| `agent-factory feature unblock <id> --to <status>` | 解除阻塞 |
| `agent-factory feature delete <id> --force` | 删除 |

### issue 命令组

| 命令 | 用途 |
|------|------|
| `agent-factory issue new --title "..." --type <bug\|feature-request> [--priority Y]` | 创建 |
| `agent-factory issue set <id> <field> [value \| --file]` | 更新 |
| `agent-factory issue show <id>` | 查看 |
| `agent-factory issue list [--status X --type Y]` | 列出 |
| `agent-factory issue transition <id> --to <status>` | 状态流转 |
| `agent-factory issue block / unblock` | 阻塞管理 |

### index 命令组

| 命令 | 用途 |
|------|------|
| `agent-factory index set feature\|issue <id> <field> <value>` | 改 priority / status / type（不允许改 title） |
| `agent-factory index refresh feature\|issue` | 扫描重建（兜底） |

### 退出码

- 0 成功
- 1 校验失败
- 2 资源不存在
- 3 状态机违规
- 4 参数错误
```

- [ ] **Step 3: 更新"创建 feature"流程描述**

找到 §新需求讨论流程（约 line 765-807），把：

```
1. PM 创建 feature：
   - index.yaml 新增行，status=draft
   - 创建 feature 目录
   - 创建 REQUIREMENTS.yaml（填入 Feature 信息，其余章节留占位）
```

改为：

```
1. PM 创建 feature（用 CLI）：
   $ agent-factory feature new --title "<title>" --agent-type <type> --priority <P>
   → CLI 自动创建 .features/<id>/REQUIREMENTS.yaml + 更新 index.yaml
```

- [ ] **Step 4: 更新"编辑字段"描述**

全文搜索"PM 在 REQUIREMENTS.yaml 写"或类似表述，改为"PM 调用 CLI 更新字段"。

例如把：
```
PM 写入对应子节
```

改为：
```
PM 调用 `agent-factory feature set <id> <field> "value"` 或 `--file <path>` 更新字段
```

- [ ] **Step 5: 更新跨环境 _incoming 流程**

找到 §跨环境 Issue 处理。生产环境 PM 创建 ISSUE.yaml 改为：

```
生产环境 PM 用 CLI（如果可用）：
  $ agent-factory issue new --title "..." --type bug --priority P1
  $ agent-factory issue set <id> scenario --file /tmp/scenario.md
  $ agent-factory issue set <id> root_cause --file /tmp/root_cause.md
  $ agent-factory issue set <id> fix_suggestion --file /tmp/fix_suggestion.md
```

如果生产环境不装 CLI，仍然允许直接编辑 YAML（手工编辑特例）。

- [ ] **Step 6: 验证 agent-pm.md 没有遗留 yaml 编辑描述**

```bash
grep -n "vim.*yaml\|直接编辑.*yaml\|手写.*yaml" agent-pm.md
```

Expected: 0 matches (除了 _incoming 流程的"生产环境特例"说明)

- [ ] **Step 7: 行数对比**

```bash
wc -l agent-pm.md
```

Expected: 行数变化不大（替换描述，不大量增删）

- [ ] **Step 8: Commit**

```bash
git add agent-pm.md
git commit -m "docs(agent-pm): teach PM to use agent-factory CLI instead of editing YAML directly"
```

---

## Task 13: 端到端验证

**Files:** 无新文件

- [ ] **Step 1: 跑全部测试**

```bash
cd system-prompt/agent-factory && python3 -m pytest agent_factory/schema/tests/ -v
```

Expected: 全部测试通过（约 70+ tests）

- [ ] **Step 2: 端到端 - 完整 feature 工作流**

```bash
cd /tmp && rm -rf test-e2e && mkdir test-e2e && cd test-e2e
mkdir .features .issues
echo "features: []" > .features/index.yaml
echo "issues: []" > .issues/index.yaml

# Create feature
agent-factory feature new --title "测试 feature"
# Expected: Created feature 1: 测试 feature

# Set fields
agent-factory feature set 1 problem "测试问题"
agent-factory feature set 1 benefit "测试收益"
agent-factory feature set 1 description "详细描述"

# Show
agent-factory feature show 1
agent-factory feature show 1 --format json

# Transition
agent-factory feature transition 1 --to designing
# Expected: Transitioned feature 1: draft → designing

# Try invalid transition (should fail - missing data_schema etc)
agent-factory feature transition 1 --to approved
# Expected: exit 1, validation error

# Fill required fields
agent-factory feature set 1 data_schema "class X: pass"
agent-factory feature set 1 interfaces "cmd add"
agent-factory feature set 1 acceptance_cases "Case 1: ..."

# Now transition
agent-factory feature transition 1 --to approved
# Expected: success

# Block
agent-factory feature block 1 --reason "等用户确认" --action "联系用户"
agent-factory feature unblock 1 --to approved

# List
agent-factory feature list
agent-factory feature list --status approved

# Delete
agent-factory feature delete 1 --force
```

- [ ] **Step 3: 端到端 - 完整 issue 工作流**

```bash
# Create issue
agent-factory issue new --title "测试 bug" --type bug --priority P1

# Set fields
agent-factory issue set 1 scenario "复现步骤"
agent-factory issue set 1 impact "影响范围"
agent-factory issue set 1 root_cause "根因分析"
agent-factory issue set 1 fix_suggestion "修复建议"

# Show
agent-factory issue show 1

# Transition
agent-factory issue transition 1 --to triaging
agent-factory issue transition 1 --to closed

# List
agent-factory issue list
```

- [ ] **Step 4: 端到端 - index 命令**

```bash
agent-factory index set feature 1 priority P1  # 如果 feature 1 还在
agent-factory index refresh feature
agent-factory index refresh issue
```

- [ ] **Step 5: 清理**

```bash
cd /tmp && rm -rf test-e2e
```

- [ ] **Step 6: 验证 agent-pm.md 没有残留旧描述**

```bash
cd /Users/zhuowentao/Workspace/repos/JoeyAssistant/skill-repo
grep -n "agent-factory-validate" system-prompt/agent-factory/agent-pm.md
# Expected: 0 matches

grep -c "agent-factory " system-prompt/agent-factory/agent-pm.md
# Expected: many (CLI 命令引用)
```

- [ ] **Step 7: 最终 commit history**

```bash
git log --oneline -15
```

Expected: 看到 13 个 commit，按 Task 1-12 顺序。

---

## Self-Review Notes

写完 plan 后 self-review：

**1. Spec coverage**：
- Design 第 2 节核心决策（PM-only / `<resource> <action>` / 参数+--file / 命令组分离 / title 同步 / 最小集 / 删 validate）→ Tasks 1-12 全覆盖
- Design 第 3 节 17 个命令：
  - feature new (Task 3) / set (Task 4) / show+list (Task 5) / transition (Task 6) / block+unblock (Task 7) / delete (Task 8) ✅
  - issue 7 命令 (Task 9) ✅
  - index set+refresh (Task 10) ✅
- Design 第 4 节错误处理 → 各任务的 exit code 实现覆盖
- Design 第 5 节状态机校验 → Task 6 完整实现
- Design 第 6 节实施层面 → 文件组织 + pyproject + 测试 全覆盖
- Design 第 7 节 agent-pm.md 集成 → Task 12
- Design 第 8 节 out of scope（add-decision / archive / migrate）→ 不实施 ✅

**2. Placeholder scan**：
- 所有 step 含完整代码或具体命令
- 无 TBD / TODO
- 测试代码完整，实现代码完整
- 端到端验证（Task 13）有具体命令

**3. Type consistency**：
- `feature_group` / `issue_group` / `index_group`：命名一致
- `find_feature_dir` / `find_issue_dir`：Task 1 定义，后续 task 使用一致
- `format_error`：Task 1 定义，所有命令使用一致
- `ALLOWED_TRANSITIONS`（feature）和 `ALLOWED_ISSUE_TRANSITIONS`：命名清晰区分
- pydantic 模型导入路径：`from agent_factory.schema import ...` 一致

**4. Type hint consistency**：
- `str | None` 在 Task 4+ 使用（Python 3.10+ 语法）。但项目 Python 3.9（pyproject.toml 设的）。
  - **Fix**: Task 1 common.py 已用 `from __future__ import annotations`，让所有 forward refs 工作。Task 4+ 的代码也需要 `from __future__ import annotations`。已包含在所有 cli/*.py 头部。

---

## Next Steps

Plan complete. 执行选择：

**1. Subagent-Driven (recommended)** - 每个 task 派 fresh subagent，task 间 review，迭代快

**2. Inline Execution** - 当前 session 内批量执行，带 checkpoint

哪种？
