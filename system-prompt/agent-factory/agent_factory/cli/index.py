# agent_factory/cli/index.py
"""index command group."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from agent_factory.cli.common import dump_yaml, format_error, load_yaml
from agent_factory.schema import FeatureIndex, FeatureIndexItem, IssueIndex, IssueIndexItem
from agent_factory.schema.enums import Priority
from agent_factory.schema.feature import FeatureStatus
from agent_factory.schema.issue import IssueStatus


# Fields that index set can modify (title NOT included - sync via feature/issue set)
INDEX_FEATURE_FIELDS = {"priority", "status"}
INDEX_ISSUE_FIELDS = {"priority", "status"}


@click.group("index")
def index_group() -> None:
    """Operate index.yaml files (.features/ .issues/).

    命令：set / refresh

    index set 支持字段：priority / status（不允许改 title——title 由
    feature/issue 创建时的 --slug 决定）

    refresh 扫描目录重建 index（兜底工具；status/priority 用默认值，
    需 PM 后续用 transition / index set 修正）
    """


@index_group.command("set")
@click.argument("resource", type=click.Choice(["feature", "issue"]))
@click.argument("item_id", type=int)
@click.argument("field")
@click.argument("value")
def set_field(resource: str, item_id: int, field: str, value: str) -> None:
    """Update an index field (priority / status). title NOT allowed."""
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
    except ValueError as exc:
        click.echo(format_error("ValidationError", str(exc), None), err=True)
        sys.exit(1)

    dump_yaml(idx_path, idx)
    click.echo(f"Updated {resource} {item_id}: {field} = {value}")


@index_group.command("refresh")
@click.argument("resource", type=click.Choice(["feature", "issue"]))
def refresh(resource: str) -> None:
    """Scan all directories and rebuild index.yaml. title = directory name."""
    import re
    base_dir = Path(f".{resource}s")
    if not base_dir.exists():
        click.echo(format_error("NotFound", f"Directory missing: {base_dir}", None), err=True)
        sys.exit(2)

    if resource == "feature":
        items = []
        for subdir in sorted(base_dir.iterdir()):
            if not subdir.is_dir():
                continue
            # Match <NNN>-<slug> or pure <id>; extract numeric id
            m = re.match(r"^(\d+)", subdir.name)
            if not m:
                continue
            feature_id = int(m.group(1))
            reqs_path = subdir / "FEATURE.yaml"
            items.append(FeatureIndexItem(
                id=feature_id,
                title=subdir.name,  # title = directory name
                status=FeatureStatus.DRAFT,  # can't infer, default
                priority=Priority.P2,
            ))
        dump_yaml(base_dir / "index.yaml", FeatureIndex(features=items))
        click.echo(f"Refreshed feature index: {len(items)} items")
    else:
        items = []
        for subdir in sorted(base_dir.iterdir()):
            if not subdir.is_dir():
                continue
            import re
            m = re.match(r"^(\d+)", subdir.name)
            if not m:
                continue
            issue_id = int(m.group(1))
            items.append(IssueIndexItem(
                id=issue_id,
                title=subdir.name,
                status=IssueStatus.OPEN,
                priority=Priority.P2,
            ))
        dump_yaml(base_dir / "index.yaml", IssueIndex(issues=items))
        click.echo(f"Refreshed issue index: {len(items)} items")
