"""Subagent 调度记录的持久化、重复回包及汇总口径。"""
from datetime import datetime, timezone
import json

from click.testing import CliRunner
import pytest

from agent_factory.cli import main
from agent_factory.cli.common import dump_yaml, load_yaml


@pytest.fixture
def run_feature(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".features" / "001-example"
    directory.mkdir(parents=True)
    path = directory / "FEATURE.yaml"
    # 存量文件：没有 subagent_runs，保留一条既有规格。
    dump_yaml(path, {
        "id": 1, "title": "001-example", "user_input": "既有需求",
        "spec": {"example": {"functions": ["既有功能"]}},
    })
    index = directory.parent / "index.yaml"
    dump_yaml(index, {"features": [{
        "id": 1, "title": "001-example", "status": "implementing", "priority": "P2",
    }]})
    return CliRunner(), path, index


def start(runner, agent="qa", task="首次验收"):
    result = runner.invoke(main, ["feature", "run", "start", "1", "--agent", agent, "--task", task])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def finish(runner, run_id, result="pass", duration=None):
    args = ["feature", "run", "finish", "1", str(run_id), "--result", result]
    if duration is not None:
        args += ["--duration-s", str(duration)]
    return runner.invoke(main, args)


def test_start_on_legacy_feature_preserves_spec_and_index(run_feature):
    runner, path, index = run_feature
    index_before = index.read_bytes()
    before = datetime.now(timezone.utc)
    record = start(runner)
    after = datetime.now(timezone.utc)
    assert record["id"] == 1
    assert record["result"] is None
    assert record["duration_s"] is None
    stamp = datetime.fromisoformat(record["dispatched_at"].replace("Z", "+00:00"))
    assert before <= stamp <= after
    data = load_yaml(path)
    assert len(data["subagent_runs"]) == 1
    assert data["spec"] == {"example": {"functions": ["既有功能"]}}
    assert index.read_bytes() == index_before


def test_retry_creates_new_record_with_next_id(run_feature):
    runner, path, _ = run_feature
    first = start(runner)
    assert finish(runner, first["id"], "fail", 120).exit_code == 0
    second = start(runner, task="复验")
    assert second["id"] == 2
    records = load_yaml(path)["subagent_runs"]
    assert records[0]["result"] == "fail"
    assert records[0]["duration_s"] == 120
    assert records[1]["result"] is None


def test_duplicate_finish_is_idempotent_and_preserves_known_time(run_feature):
    runner, path, _ = run_feature
    record = start(runner)
    first = finish(runner, record["id"], duration=0)
    assert first.exit_code == 0, first.output
    saved = path.read_bytes()
    second = finish(runner, record["id"], duration=0)
    assert second.exit_code == 0, second.output
    assert first.output == second.output
    assert path.read_bytes() == saved
    # 回包未携带耗时时，也不能清空已记录的 0 秒。
    assert finish(runner, record["id"]).exit_code == 0
    assert path.read_bytes() == saved
    assert len(load_yaml(path)["subagent_runs"]) == 1


@pytest.mark.parametrize("result", ["complete", "pass", "fail", "lock_busy", "interrupted"])
def test_missing_duration_stays_unknown(run_feature, result):
    runner, path, _ = run_feature
    record = start(runner, agent="developer" if result == "complete" else "qa")
    response = finish(runner, record["id"], result)
    assert response.exit_code == 0, response.output
    data = load_yaml(path)["subagent_runs"][0]
    assert data["result"] == result
    assert data["duration_s"] is None


def test_can_fill_unknown_duration_for_same_result(run_feature):
    runner, path, _ = run_feature
    record = start(runner)
    assert finish(runner, record["id"], "fail").exit_code == 0
    response = finish(runner, record["id"], "fail", 125)
    assert response.exit_code == 0, response.output
    assert load_yaml(path)["subagent_runs"][0]["duration_s"] == 125


@pytest.mark.parametrize("result,duration", [("fail", 30), ("pass", 31)])
def test_conflicting_reply_cannot_overwrite_existing_result(run_feature, result, duration):
    runner, path, _ = run_feature
    record = start(runner)
    assert finish(runner, record["id"], duration=30).exit_code == 0
    saved = path.read_bytes()
    response = finish(runner, record["id"], result, duration)
    assert response.exit_code == 3
    assert path.read_bytes() == saved


def test_other_feature_updates_preserve_run_history(run_feature):
    runner, path, _ = run_feature
    record = start(runner)
    assert finish(runner, record["id"], "fail", 17).exit_code == 0
    saved = load_yaml(path)["subagent_runs"]
    response = runner.invoke(main, ["feature", "set", "1", "user_input", "更新的需求"])
    assert response.exit_code == 0, response.output
    assert load_yaml(path)["subagent_runs"] == saved
    for field in ["subagent_runs", "subagent_runs.1.duration_s"]:
        response = runner.invoke(main, ["feature", "set", "1", field, "[]"])
        assert response.exit_code == 4
    assert load_yaml(path)["subagent_runs"] == saved


@pytest.mark.parametrize("args", [
    ["start", "1", "--agent", "unknown", "--task", "验收"],
    ["finish", "1", "1", "--result", "unknown"],
    ["finish", "1", "1", "--result", "pass", "--duration-s", "-1"],
    ["finish", "1", "1", "--result", "pass", "--duration-s", "1.5"],
    ["finish", "1", "0", "--result", "pass"],
])
def test_invalid_arguments_leave_feature_unchanged(run_feature, args):
    runner, path, _ = run_feature
    saved = path.read_bytes()
    response = runner.invoke(main, ["feature", "run"] + args)
    assert response.exit_code == 4
    assert path.read_bytes() == saved


def test_blank_task_leaves_feature_unchanged(run_feature):
    runner, path, _ = run_feature
    saved = path.read_bytes()
    response = runner.invoke(main, ["feature", "run", "start", "1", "--agent", "qa", "--task", "  "])
    assert response.exit_code == 1
    assert path.read_bytes() == saved


def test_missing_feature_and_run_return_not_found(run_feature):
    runner, path, _ = run_feature
    saved = path.read_bytes()
    args = ["feature", "run", "start", "999", "--agent", "qa", "--task", "验收"]
    assert runner.invoke(main, args).exit_code == 2
    assert runner.invoke(main, ["feature", "run", "finish", "999", "1", "--result", "pass"]).exit_code == 2
    assert finish(runner, 1).exit_code == 2
    assert path.read_bytes() == saved


def test_summary_excludes_unknown_times_and_keeps_retries(run_feature):
    runner, path, _ = run_feature
    first = start(runner, "developer", "首次实现")
    assert finish(runner, first["id"], "complete", 30).exit_code == 0
    second = start(runner, "developer", "修复 QA 问题")
    assert finish(runner, second["id"], "fail", 0).exit_code == 0
    third = start(runner, "developer", "重试实现")
    assert finish(runner, third["id"], "interrupted").exit_code == 0
    start(runner, "qa", "首次验收")
    response = runner.invoke(main, ["feature", "show", "1"])
    assert response.exit_code == 0, response.output
    assert "| developer | 3 | 2 | 1 | 30 | 15.0 | 1 |" in response.output
    assert "| qa | 1 | 0 | 1 | 0 | 未知 | 0 |" in response.output
    assert "进行中 / 待核实" in response.output
    assert "累计耗时不等于用户等待时间" in response.output
    response = runner.invoke(main, ["feature", "show", "1", "--format", "json"])
    assert response.exit_code == 0
    assert len(json.loads(response.output)["subagent_runs"]) == 4
    assert "subagent_summary" not in load_yaml(path)


@pytest.mark.parametrize("cmd", [[], ["start"], ["finish"]])
def test_run_commands_have_help(run_feature, cmd):
    runner, _, _ = run_feature
    response = runner.invoke(main, ["feature", "run"] + cmd + ["--help"])
    assert response.exit_code == 0
