# agent_factory/cli/issue.py
"""issue command group. Mirrors feature command group structure."""
from __future__ import annotations

import json
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


@click.group("issue")
def issue_group() -> None:
    """Operate issue ISSUE.yaml."""


# Note: 'title' is NOT in this set -- title is immutable (equals directory name)
ISSUE_FIELDS = {
    "scenario", "impact",
    "root_cause", "fix_suggestion", "fix", "resolution",
}


@issue_group.command("new")
@click.option("--title", required=True, help="Human-readable title (stored in ISSUE.yaml)")
@click.option("--slug", required=True, help="Directory slug (kebab-case)")
@click.option("--type", "issue_type", required=True,
              type=click.Choice([t.value for t in IssueType]),
              help="Issue type (bug / feature-request)")
@click.option("--priority", default=Priority.P2.value,
              type=click.Choice([p.value for p in Priority]),
              help="Priority (default: P2)")
def new(title: str, slug: str, issue_type: str, priority: str) -> None:
    """Create new issue (status=open).

    Directory name: <NNN>-<slug> (e.g., 001-login-crash).
    """
    import re
    if not re.match(r"^[a-z][a-z0-9-]*$", slug):
        click.echo(format_error("InvalidSlug", f"Slug must be kebab-case: {slug}", None), err=True)
        sys.exit(4)

    issue_id = next_issue_id()
    dir_name = f"{issue_id:03d}-{slug}"
    issue_dir = Path(".issues") / dir_name
    if issue_dir.exists():
        click.echo(format_error("FileExists", f"Directory already exists: {issue_dir}", str(issue_dir)), err=True)
        sys.exit(1)

    try:
        issue = Issue(
            id=issue_id,
            title=dir_name,
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
        title=dir_name,
        type=IssueType(issue_type),
        status=IssueStatus.OPEN,
        priority=Priority(priority),
    ))
    dump_yaml(idx_path, idx)

    click.echo(f"Created issue {issue_id}: {dir_name}")


@issue_group.command("set")
@click.argument("issue_id", type=int)
@click.argument("field")
@click.argument("value", required=False)
@click.option("--file", "file_path", type=click.Path(exists=True, path_type=Path),
              help="Read value from file")
def set_field(issue_id: int, field: str, value: str | None, file_path: Path | None) -> None:
    """Update a field in ISSUE.yaml. Title is immutable (equals directory name)."""
    if field not in ISSUE_FIELDS:
        click.echo(format_error("InvalidField",
                                f"Field '{field}' not supported. Valid: {sorted(ISSUE_FIELDS)}",
                                None), err=True)
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
        lines = [f"# Issue {issue.id}: {issue.title}", ""]
        lines += ["## Scenario", issue.scenario, ""]
        lines += ["## Impact", issue.impact, ""]
        if issue.root_cause:
            lines += ["## Root Cause", issue.root_cause, ""]
        if issue.fix_suggestion:
            lines += ["## Fix Suggestion", issue.fix_suggestion, ""]
        if issue.fix:
            lines += ["## Fix", issue.fix, ""]
        if issue.resolution:
            lines += ["## Resolution", issue.resolution, ""]
        click.echo("\n".join(lines))


@issue_group.command("list")
@click.option("--status", type=click.Choice([s.value for s in IssueStatus]), help="Filter by status")
@click.option("--type", "issue_type", type=click.Choice([t.value for t in IssueType]),
              help="Filter by type")
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
            click.echo(f"{item.id:<5} {item.type.value:<18} {item.status.value:<10} "
                       f"{item.priority.value:<10} {item.title}")


# Issue state machine: open → triaging → closed
ALLOWED_ISSUE_TRANSITIONS = {
    IssueStatus.OPEN: {IssueStatus.TRIAGING, IssueStatus.CLOSED},
    IssueStatus.TRIAGING: {IssueStatus.CLOSED, IssueStatus.OPEN},
    IssueStatus.CLOSED: set(),
}


@issue_group.command("transition")
@click.argument("issue_id", type=int)
@click.option("--to", "target", required=True,
              type=click.Choice([s.value for s in IssueStatus]))
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
@click.option("--reason", required=True, help="Why blocked")
@click.option("--action", "action_text", required=True, help="What's needed to unblock")
def block(issue_id: int, reason: str, action_text: str) -> None:
    """Block issue (creates BLOCKED.yaml, keeps status=triaging)."""
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    blocked_path = issue_dir / "BLOCKED.yaml"
    if blocked_path.exists():
        click.echo(format_error("AlreadyBlocked",
                                f"Issue {issue_id} already blocked",
                                str(blocked_path)), err=True)
        sys.exit(1)

    dump_yaml(blocked_path, BlockedRecord(reason=reason, action=action_text))

    # Issue has no dedicated blocked status; keep triaging
    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    for item in idx.issues:
        if item.id == issue_id:
            item.status = IssueStatus.TRIAGING
            break
    dump_yaml(idx_path, idx)

    click.echo(f"Blocked issue {issue_id}: {reason[:50]}")


@issue_group.command("unblock")
@click.argument("issue_id", type=int)
@click.option("--to", "target", required=True,
              type=click.Choice([s.value for s in IssueStatus]))
def unblock(issue_id: int, target: str) -> None:
    """Unblock issue (removes BLOCKED.yaml + sets status to --to)."""
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
