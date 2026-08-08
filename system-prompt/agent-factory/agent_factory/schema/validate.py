# agent_factory/schema/validate.py
"""YAML 文件 schema 校验 CLI.

用法:
    python -m agent_factory.schema.validate <path>

扫描路径下所有 .yaml 文件，按文件名识别类型并校验。
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from pydantic import ValidationError

from agent_factory.schema.feature import Feature
from agent_factory.schema.issue import Issue
from agent_factory.schema.index import FeatureIndex, IssueIndex
from agent_factory.schema.blocked import BlockedRecord


def _load_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def _format_error(path: Path, exc: ValidationError) -> str:
    lines = [f"❌ {path}"]
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"])
        lines.append(f"  {loc}: {err['msg']}")
    return "\n".join(lines)


def validate_feature(path: Path) -> None:
    """校验 REQUIREMENTS.yaml."""
    try:
        Feature.model_validate(_load_yaml(path))
    except ValidationError as exc:
        click.echo(_format_error(path, exc), err=True)
        sys.exit(1)


def validate_issue(path: Path) -> None:
    """校验 ISSUE.yaml."""
    try:
        Issue.model_validate(_load_yaml(path))
    except ValidationError as exc:
        click.echo(_format_error(path, exc), err=True)
        sys.exit(1)


def validate_feature_index(path: Path) -> None:
    """校验 .features/index.yaml."""
    try:
        FeatureIndex.model_validate(_load_yaml(path))
    except ValidationError as exc:
        click.echo(_format_error(path, exc), err=True)
        sys.exit(1)


def validate_issue_index(path: Path) -> None:
    """校验 .issues/index.yaml."""
    try:
        IssueIndex.model_validate(_load_yaml(path))
    except ValidationError as exc:
        click.echo(_format_error(path, exc), err=True)
        sys.exit(1)


def validate_blocked(path: Path) -> None:
    """校验 BLOCKED.yaml."""
    try:
        BlockedRecord.model_validate(_load_yaml(path))
    except ValidationError as exc:
        click.echo(_format_error(path, exc), err=True)
        sys.exit(1)


def _validate_by_filename(path: Path) -> Optional[str]:
    """按文件名识别类型并校验。返回校验状态字符串或 None."""
    name = path.name
    parent_name = path.parent.name

    if name == "REQUIREMENTS.yaml":
        validate_feature(path)
        return f"✓ {path} (feature)"
    elif name == "ISSUE.yaml":
        validate_issue(path)
        return f"✓ {path} (issue)"
    elif name == "BLOCKED.yaml":
        validate_blocked(path)
        return f"✓ {path} (blocked)"
    elif name == "index.yaml":
        if parent_name == ".features":
            validate_feature_index(path)
            return f"✓ {path} (feature index)"
        elif parent_name == ".issues":
            validate_issue_index(path)
            return f"✓ {path} (issue index)"
    return None


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def main(path: Path) -> None:
    """扫描 PATH 下所有 YAML 文件并校验."""
    if path.is_file():
        if path.suffix not in (".yaml", ".yml"):
            click.echo(f"⚠ {path} 非 YAML 文件，跳过")
            return
        result = _validate_by_filename(path)
        if result:
            click.echo(result)
        else:
            click.echo(f"⚠ {path} 未识别的文件名，跳过")
        return

    yaml_files = sorted(path.rglob("*.yaml"))
    if not yaml_files:
        click.echo(f"⚠ {path} 下无 YAML 文件")
        return

    validated = 0
    skipped = 0
    for f in yaml_files:
        result = _validate_by_filename(f)
        if result:
            click.echo(result)
            validated += 1
        else:
            skipped += 1

    click.echo(f"\n校验完成: {validated} 通过, {skipped} 跳过")


if __name__ == "__main__":
    main()
