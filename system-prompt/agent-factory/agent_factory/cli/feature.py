# agent_factory/cli/feature.py
"""feature command group."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from agent_factory.cli.common import (
    dump_yaml, find_feature_dir, format_error, load_yaml, next_feature_id,
)
from agent_factory.schema import Feature, FeatureIndex, FeatureIndexItem
from agent_factory.schema.enums import AgentType, FeatureStatus, Priority


@click.group("feature")
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


# State machine: allowed transitions
ALLOWED_TRANSITIONS = {
    FeatureStatus.DRAFT: {FeatureStatus.DESIGNING, FeatureStatus.CANCELLED},
    FeatureStatus.DESIGNING: {FeatureStatus.APPROVED, FeatureStatus.BLOCKED, FeatureStatus.CANCELLED},
    FeatureStatus.APPROVED: {FeatureStatus.IMPLEMENTING, FeatureStatus.CANCELLED},
    FeatureStatus.IMPLEMENTING: {FeatureStatus.QA_REVIEWING, FeatureStatus.BLOCKED},
    FeatureStatus.QA_REVIEWING: {FeatureStatus.DONE, FeatureStatus.IMPLEMENTING},  # QA fail → implementing
    FeatureStatus.BLOCKED: set(),  # needs unblock command
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
