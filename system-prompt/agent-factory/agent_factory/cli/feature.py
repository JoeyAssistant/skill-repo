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
