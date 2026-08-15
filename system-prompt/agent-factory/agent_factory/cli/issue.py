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
from agent_factory.schema.enums import IssueStatus, Priority
from agent_factory.schema.issue import BugfixResult, FeatureRequestResult


def _issue_doc() -> str:
    """读 doc/issue.md 原文作为 group help（设计文档 = help 唯一真值）.

    click 会对 help 文本按段落 rewrap（换行被压扁）；在每个段落前插 \\b
    标记可让该段原样输出，保留 issue.md 的原始换行。
    """
    p = Path(__file__).resolve().parent.parent / "doc" / "issue.md"
    if not p.exists():
        return "Operate issue ISSUE.yaml."
    return "\n\b\n" + p.read_text().replace("\n\n", "\n\n\b\n")


@click.group("issue", help=_issue_doc())
def issue_group() -> None:
    """Operate issue ISSUE.yaml."""


# Note: 'title' is NOT in this set -- title is immutable (equals directory name)
# Note: 'result' is special — use `issue close` command instead of `set` for it
ISSUE_FIELDS = {
    "desc", "scenario", "impact",
    "root_cause", "fix_plan",
}


@issue_group.command("new")
@click.option("--title", required=True, help="Human-readable title (stored in ISSUE.yaml)")
@click.option("--slug", required=True, help="Directory slug (kebab-case)")
@click.option("--desc", required=True, help="User's original description (preserved verbatim)")
@click.option("--priority", default=Priority.P2.value,
              type=click.Choice([p.value for p in Priority]),
              help="Priority (default: P2)")
def new(title: str, slug: str, desc: str, priority: str) -> None:
    """Create new issue (status=open).

    Directory name: <NNN>-<slug> (e.g., 001-login-crash).
    --desc preserves user's original description verbatim (required).
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
            desc=desc,
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
        lines += ["## Description", issue.desc, ""]
        if issue.scenario:
            lines += ["## Scenario", issue.scenario, ""]
        if issue.impact:
            lines += ["## Impact", issue.impact, ""]
        if issue.root_cause:
            lines += ["## Root Cause", issue.root_cause, ""]
        if issue.fix_plan:
            lines += ["## Fix Plan", issue.fix_plan, ""]
        if issue.result:
            if isinstance(issue.result, BugfixResult):
                lines += ["## Result (bugfix)",
                          f"**fix_desc**: {issue.result.fix_desc}", "",
                          f"**verification**: {issue.result.verification}", ""]
            elif isinstance(issue.result, FeatureRequestResult):
                lines += ["## Result (feature_request)",
                          f"**feature_id**: {issue.result.feature_id}", ""]
        click.echo("\n".join(lines))


@issue_group.command("list")
@click.option("--status", type=click.Choice([s.value for s in IssueStatus]),
              help="Filter by status")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def list_issues(status: str | None, fmt: str) -> None:
    """List issues."""
    idx_path = Path(".issues") / "index.yaml"
    if not idx_path.exists():
        click.echo("No issues found.")
        return

    idx = IssueIndex.model_validate(load_yaml(idx_path))
    items = idx.issues
    if status:
        items = [i for i in items if i.status.value == status]

    if fmt == "json":
        click.echo(json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'ID':<5} {'STATUS':<12} {'PRIORITY':<10} TITLE")
        for item in items:
            click.echo(f"{item.id:<5} {item.status.value:<12} {item.priority.value:<10} {item.title}")


# Issue state machine: open → in_progress → closed
ALLOWED_ISSUE_TRANSITIONS = {
    IssueStatus.OPEN: {IssueStatus.IN_PROGRESS, IssueStatus.CLOSED},
    IssueStatus.IN_PROGRESS: {IssueStatus.CLOSED, IssueStatus.OPEN},
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

    # Cross-field validation: open → in_progress requires scenario + impact
    if current_status == IssueStatus.OPEN and target_status == IssueStatus.IN_PROGRESS:
        issue = Issue.model_validate(load_yaml(issue_dir / "ISSUE.yaml"))
        missing = []
        if not (issue.scenario or "").strip():
            missing.append("scenario is empty (PM must fill via `agent-factory issue set <id> scenario ...`)")
        if not (issue.impact or "").strip():
            missing.append("impact is empty (PM must fill via `agent-factory issue set <id> impact ...`)")
        if missing:
            click.echo(format_error(
                "ValidationError",
                "Cannot start in_progress (PM 信息收集未完成): " + "; ".join(missing),
                str(issue_dir / "ISSUE.yaml"),
            ), err=True)
            sys.exit(1)

    # Cross-field validation: in_progress → closed requires root_cause + fix_plan + result
    if current_status == IssueStatus.IN_PROGRESS and target_status == IssueStatus.CLOSED:
        issue = Issue.model_validate(load_yaml(issue_dir / "ISSUE.yaml"))
        missing = []
        if not (issue.root_cause or "").strip():
            missing.append("root_cause is empty (QA must fill)")
        if not (issue.fix_plan or "").strip():
            missing.append("fix_plan is empty (QA must fill)")
        if not issue.result:
            missing.append("result is empty (use `agent-factory issue close` command)")
        if missing:
            click.echo(format_error(
                "ValidationError",
                "Cannot close issue: " + "; ".join(missing),
                str(issue_dir / "ISSUE.yaml"),
            ), err=True)
            sys.exit(1)

    current_item.status = target_status
    dump_yaml(idx_path, idx)

    click.echo(f"Transitioned issue {issue_id}: {current_status.value} → {target_status.value}")


@issue_group.command("close")
@click.argument("issue_id", type=int)
@click.option("--bugfix", "is_bugfix", is_flag=True, help="Close as bugfix")
@click.option("--feature-request", "is_feature_request", is_flag=True, help="Close as feature_request")
@click.option("--fix-desc", help="(bugfix) modification content")
@click.option("--verification", help="(bugfix) PM verification result")
@click.option("--feature-id", type=int, help="(feature_request) target feature id")
def close(issue_id: int, is_bugfix: bool, is_feature_request: bool,
          fix_desc: str | None, verification: str | None, feature_id: int | None) -> None:
    """Close issue with result (one-step: fill result + transition to closed)."""
    if is_bugfix == is_feature_request:
        click.echo(format_error(
            "InvalidArgs",
            "Must specify exactly one of --bugfix or --feature-request",
            None,
        ), err=True)
        sys.exit(4)

    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    # Build result object
    if is_bugfix:
        if not fix_desc or not verification:
            click.echo(format_error(
                "InvalidArgs",
                "--bugfix requires --fix-desc and --verification",
                None,
            ), err=True)
            sys.exit(4)
        result = BugfixResult(fix_desc=fix_desc, verification=verification)
    else:  # feature_request
        if feature_id is None:
            click.echo(format_error(
                "InvalidArgs",
                "--feature-request requires --feature-id",
                None,
            ), err=True)
            sys.exit(4)
        result = FeatureRequestResult(feature_id=feature_id)

    # Write result to ISSUE.yaml
    issue_path = issue_dir / "ISSUE.yaml"
    try:
        data = load_yaml(issue_path)
        data["result"] = result.model_dump(mode="json")
        issue = Issue.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(issue_path)), err=True)
        sys.exit(1)
    dump_yaml(issue_path, issue)

    # Transition to closed (will run cross-field validation including result)
    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    current_item = next((i for i in idx.issues if i.id == issue_id), None)
    if not current_item:
        click.echo(format_error("NotFound", f"Issue {issue_id} not in index", None), err=True)
        sys.exit(2)

    current_status = current_item.status
    if IssueStatus.CLOSED not in ALLOWED_ISSUE_TRANSITIONS.get(current_status, set()):
        click.echo(format_error(
            "InvalidTransition",
            f"Path '{current_status.value} → closed' is not allowed",
            None,
        ), err=True)
        sys.exit(3)

    # Cross-field validation (same as transition command)
    if current_status == IssueStatus.IN_PROGRESS:
        issue_data = Issue.model_validate(load_yaml(issue_path))
        missing = []
        if not (issue_data.root_cause or "").strip():
            missing.append("root_cause is empty (QA must fill)")
        if not (issue_data.fix_plan or "").strip():
            missing.append("fix_plan is empty (QA must fill)")
        if missing:
            click.echo(format_error(
                "ValidationError",
                "Cannot close issue: " + "; ".join(missing),
                str(issue_path),
            ), err=True)
            sys.exit(1)

    current_item.status = IssueStatus.CLOSED
    dump_yaml(idx_path, idx)

    result_type = "bugfix" if is_bugfix else "feature_request"
    click.echo(f"Closed issue {issue_id} as {result_type}")


@issue_group.command("block")
@click.argument("issue_id", type=int)
@click.option("--reason", required=True, help="Why blocked")
@click.option("--action", "action_text", required=True, help="What's needed to unblock")
def block(issue_id: int, reason: str, action_text: str) -> None:
    """Block issue (creates BLOCKED.yaml, keeps status=in_progress)."""
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

    # Issue has no dedicated blocked status; keep in_progress
    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    for item in idx.issues:
        if item.id == issue_id:
            item.status = IssueStatus.IN_PROGRESS
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
