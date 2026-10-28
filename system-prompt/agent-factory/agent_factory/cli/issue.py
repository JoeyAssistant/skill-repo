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
    dump_yaml, find_issue_dir, format_error, load_yaml, next_feature_id,
    next_issue_id,
)
from agent_factory.schema import (
    ClosedResult, ConvertedResult, Feature, FeatureIndex,
    FeatureIndexItem, FeatureStatus, Issue, IssueCloseReason, IssueIndex,
    IssueIndexItem,
)
from agent_factory.schema.enums import Priority
from agent_factory.schema.issue import IssueStatus


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
    "user_input", "summary", "scenario", "repro_steps", "impact",
    "root_cause", "evidence", "log_gap", "fix_plan",
}


@issue_group.command("new")
@click.option("--title", required=True, help="Human-readable title (stored in ISSUE.yaml)")
@click.option("--slug", required=True, help="Directory slug (kebab-case)")
@click.option("--user-input", required=True, help="User's original input (preserved verbatim)")
@click.option("--priority", default=Priority.P2.value,
              type=click.Choice([p.value for p in Priority]),
              help="Priority (default: P2)")
@click.option("--summary", default=None,
              help="一句话总结（≤50 字）：什么问题/现象+影响（后续可用 issue set 补）")
def new(title: str, slug: str, user_input: str, priority: str, summary: str | None) -> None:
    """Create new issue (status=open).

    Directory name: <NNN>-<slug> (e.g., 001-login-crash).
    --user-input preserves user's original description verbatim (required).
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
            user_input=user_input,
            summary=summary,
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
    """Update a field in ISSUE.yaml. Title is immutable (equals directory name).

    传值约定：多行长文本（user_input / scenario / repro_steps / evidence / impact /
    root_cause / log_gap / fix_plan 等）统一 `--file <path>` 传值——
    inline 传参在含引号 / $ / 反引号 / # 时 shell 转义不可靠，内容会静默截断或损坏；
    --file 原样读入零转义。evidence 需传 YAML 列表。
    """
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

    if field == "evidence":
        try:
            parsed = yaml.safe_load(new_value)
        except yaml.YAMLError as exc:
            click.echo(format_error("InvalidValue",
                                    f"evidence 必须是 YAML 列表: {exc}", None), err=True)
            sys.exit(4)
        if not isinstance(parsed, list):
            click.echo(format_error(
                "InvalidValue",
                "evidence 必须是 YAML 列表，每项为 "
                "{step, claim, type, locator, snippet}", None), err=True)
            sys.exit(4)
        field_value = parsed
    else:
        field_value = new_value

    issue_path = issue_dir / "ISSUE.yaml"
    try:
        data = load_yaml(issue_path)
        data[field] = field_value
        issue = Issue.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(issue_path)), err=True)
        sys.exit(1)

    dump_yaml(issue_path, issue)

    click.echo(f"Updated issue {issue_id}: {field}")


def _feature_status_map() -> dict[int, str]:
    """Map feature id -> status from .features/index.yaml (derived view)."""
    p = Path(".features") / "index.yaml"
    if not p.exists():
        return {}
    idx = FeatureIndex.model_validate(load_yaml(p))
    return {i.id: i.status.value for i in idx.features}


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
        if issue.summary:
            lines += [f"**Summary**: {issue.summary}", ""]
        lines += ["## User Input", issue.user_input, ""]
        if issue.scenario:
            lines += ["## Scenario", issue.scenario, ""]
        if issue.repro_steps:
            lines += ["## Repro Steps", issue.repro_steps, ""]
        if issue.impact:
            lines += ["## Impact", issue.impact, ""]
        if issue.root_cause:
            lines += ["## Root Cause", issue.root_cause, ""]
        if issue.evidence:
            lines += ["## Evidence", ""]
            for ev in issue.evidence:
                lines.append(f"{ev.step}. [{ev.type.value}] {ev.claim}")
                lines.append(f"   - locator: {ev.locator}")
                lines.append("   - snippet:")
                for snippet_line in ev.snippet.rstrip("\n").splitlines():
                    lines.append(f"     {snippet_line}")
                lines.append("")
        if issue.log_gap:
            lines += ["## Log Gap", issue.log_gap, ""]
        if issue.fix_plan:
            lines += ["## Fix Plan", issue.fix_plan, ""]
        if issue.result:
            if isinstance(issue.result, ConvertedResult):
                lines += ["## Result (converted_to_feature)",
                          f"**feature_id**: {issue.result.feature_id}"]
                feature_status = _feature_status_map().get(issue.result.feature_id)
                if feature_status:
                    lines += [f"**feature_status**: {feature_status}"]
                lines += [""]
            elif isinstance(issue.result, ClosedResult):
                lines += ["## Result (closed)",
                          f"**reason_type**: {issue.result.reason_type.value}", "",
                          f"**reason**: {issue.result.reason}", ""]
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

    feature_status = _feature_status_map()

    def _issue_brief(item: IssueIndexItem) -> tuple[str | None, int | None, str | None]:
        """Return (summary, feature_id, feature_status) read from ISSUE.yaml."""
        try:
            issue = Issue.model_validate(load_yaml(Path(".issues") / item.title / "ISSUE.yaml"))
        except Exception:
            return None, None, None
        if isinstance(issue.result, ConvertedResult):
            return issue.summary, issue.result.feature_id, feature_status.get(issue.result.feature_id)
        return issue.summary, None, None

    if fmt == "json":
        rows = []
        for item in items:
            row = item.model_dump(mode="json")
            summary, fid, fstatus = _issue_brief(item)
            row["summary"] = summary
            if fid is not None:
                row["feature_id"] = fid
                row["feature_status"] = fstatus
            rows.append(row)
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'ID':<5} {'STATUS':<12} {'PRIORITY':<10} {'FEATURE':<20} {'TITLE':<40} SUMMARY")
        for item in items:
            summary, fid, fstatus = _issue_brief(item)
            ref = f"#{fid}({fstatus})" if fid is not None and fstatus else (f"#{fid}" if fid is not None else "-")
            click.echo(f"{item.id:<5} {item.status.value:<12} {item.priority.value:<10} {ref:<20} {item.title:<40} {summary or '-'}")


# Issue state machine: open → in_progress → closed
ALLOWED_ISSUE_TRANSITIONS = {
    IssueStatus.OPEN: {IssueStatus.IN_PROGRESS, IssueStatus.CLOSED},
    IssueStatus.IN_PROGRESS: {IssueStatus.CLOSED, IssueStatus.OPEN},
    IssueStatus.CLOSED: set(),
}


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def _missing_diagnosis(issue: Issue) -> list[str]:
    """Return missing diagnosis-field messages (qa proposes, PM confirms and writes)."""
    missing: list[str] = []
    for field in ("root_cause", "fix_plan", "repro_steps", "log_gap"):
        if not _has_text(getattr(issue, field)):
            missing.append(
                f"{field} is empty (qa-diagnosis proposes, PM confirms and fills)")
    return missing


def _validate_close(issue: Issue, current_status: IssueStatus) -> list[str]:
    """Return missing-field messages for closing an issue."""
    if issue.result is None:
        return ["result is empty (use `agent-factory issue close` or `agent-factory issue convert`)"]
    missing: list[str] = []
    if isinstance(issue.result, ConvertedResult):
        if current_status != IssueStatus.IN_PROGRESS:
            missing.append("convert requires in_progress")
        missing.extend(_missing_diagnosis(issue))
    elif isinstance(issue.result, ClosedResult):
        if not issue.result.reason.strip():
            missing.append("reason is empty")
        if issue.result.reason_type == IssueCloseReason.NO_ACTION:
            missing.extend(_missing_diagnosis(issue))
    return missing


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

    # Cross-field validation: open → in_progress requires summary + scenario + impact
    if current_status == IssueStatus.OPEN and target_status == IssueStatus.IN_PROGRESS:
        issue = Issue.model_validate(load_yaml(issue_dir / "ISSUE.yaml"))
        missing = []
        if not _has_text(issue.summary):
            missing.append("summary is empty (PM must confirm with user and fill via `issue set`)")
        if not _has_text(issue.scenario):
            missing.append("scenario is empty (PM must confirm with user and fill via `issue set`)")
        if not _has_text(issue.impact):
            missing.append("impact is empty (PM must confirm with user and fill via `issue set`)")
        if missing:
            click.echo(format_error(
                "ValidationError",
                "Cannot start in_progress (PM 信息收集未完成): " + "; ".join(missing),
                str(issue_dir / "ISSUE.yaml"),
            ), err=True)
            sys.exit(1)

    # Cross-field validation: closed requires a valid result
    if target_status == IssueStatus.CLOSED:
        issue = Issue.model_validate(load_yaml(issue_dir / "ISSUE.yaml"))
        missing = _validate_close(issue, current_status)
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
@click.option("--reason-type", "reason_type", required=True,
              type=click.Choice([r.value for r in IssueCloseReason]),
              help="Close reason category")
@click.option("--reason", required=True, help="Close reason detail")
def close(issue_id: int, reason_type: str, reason: str) -> None:
    """Close issue without a feature (duplicate / invalid / wontfix / no_action).

    Use `issue convert` when the issue requires a code change.
    """
    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    issue_path = issue_dir / "ISSUE.yaml"
    try:
        data = load_yaml(issue_path)
        data["result"] = ClosedResult(
            reason_type=IssueCloseReason(reason_type),
            reason=reason,
        ).model_dump(mode="json")
        issue = Issue.model_validate(data)
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(issue_path)), err=True)
        sys.exit(1)

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

    missing = _validate_close(issue, current_status)
    if missing:
        click.echo(format_error(
            "ValidationError",
            "Cannot close issue: " + "; ".join(missing),
            str(issue_path),
        ), err=True)
        sys.exit(1)

    dump_yaml(issue_path, issue)
    current_item.status = IssueStatus.CLOSED
    dump_yaml(idx_path, idx)
    click.echo(f"Closed issue {issue_id} as {reason_type}")


@issue_group.command("convert")
@click.argument("issue_id", type=int)
@click.option("--slug", required=True, help="Feature directory slug (kebab-case)")
def convert(issue_id: int, slug: str) -> None:
    """Convert issue to feature and close it as converted_to_feature.

    Requires the issue to be in_progress with root_cause + fix_plan +
    repro_steps + log_gap filled (qa-diagnosis proposes, PM confirms).
    Creates a feature from user_input and links source_issue.
    """
    import re
    if not re.match(r"^[a-z][a-z0-9-]*$", slug):
        click.echo(format_error(
            "InvalidSlug",
            f"Slug must be kebab-case: {slug}",
            None,
        ), err=True)
        sys.exit(4)

    try:
        issue_dir = find_issue_dir(issue_id)
    except FileNotFoundError as exc:
        click.echo(format_error("NotFound", str(exc), None), err=True)
        sys.exit(2)

    issue_path = issue_dir / "ISSUE.yaml"
    try:
        issue = Issue.model_validate(load_yaml(issue_path))
    except ValidationError as exc:
        click.echo(format_error("ValidationError", str(exc), str(issue_path)), err=True)
        sys.exit(1)

    idx_path = Path(".issues") / "index.yaml"
    idx = IssueIndex.model_validate(load_yaml(idx_path))
    current_item = next((i for i in idx.issues if i.id == issue_id), None)
    if not current_item:
        click.echo(format_error("NotFound", f"Issue {issue_id} not in index", None), err=True)
        sys.exit(2)

    if current_item.status != IssueStatus.IN_PROGRESS:
        click.echo(format_error(
            "InvalidTransition",
            f"Convert requires in_progress, current: {current_item.status.value}",
            None,
        ), err=True)
        sys.exit(3)

    missing = _missing_diagnosis(issue)
    if missing:
        click.echo(format_error(
            "ValidationError",
            "Cannot convert issue: " + "; ".join(missing),
            str(issue_path),
        ), err=True)
        sys.exit(1)

    feature_id = next_feature_id()
    dir_name = f"{feature_id:03d}-{slug}"
    feature_dir = Path(".features") / dir_name
    if feature_dir.exists():
        click.echo(format_error(
            "FileExists",
            f"Directory already exists: {feature_dir}",
            str(feature_dir),
        ), err=True)
        sys.exit(1)

    feature = Feature(
        id=feature_id,
        title=dir_name,
        user_input=issue.user_input,
        source_issue=issue.id,
    )
    feature_dir.mkdir(parents=True)
    dump_yaml(feature_dir / "FEATURE.yaml", feature)

    feat_idx_path = Path(".features") / "index.yaml"
    feat_idx = FeatureIndex.model_validate(load_yaml(feat_idx_path)) if feat_idx_path.exists() else FeatureIndex()
    feat_idx.features.append(FeatureIndexItem(
        id=feature_id,
        title=dir_name,
        status=FeatureStatus.DRAFT,
        priority=current_item.priority,
    ))
    dump_yaml(feat_idx_path, feat_idx)

    issue.result = ConvertedResult(feature_id=feature_id)
    dump_yaml(issue_path, issue)
    current_item.status = IssueStatus.CLOSED
    dump_yaml(idx_path, idx)

    click.echo(f"Converted issue {issue_id} to feature {feature_id}: {dir_name}")
