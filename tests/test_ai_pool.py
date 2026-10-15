import contextlib
from types import SimpleNamespace

import pytest
from conftest import FakeLauncher, writes
from cursor_sdk import CursorAgentError

from summary.ai_pool import (
    AgentRunError,
    AIPool,
    BridgeLaunchError,
    MissingApiKeyError,
    PoolError,
    RulesFileError,
    RunDirError,
    SummaryError,
)
from summary.ai_pool.cursor import CursorAgentLauncher
from summary.ai_pool.cursor import launcher as launcher_module
from summary.ai_pool.cursor import session as session_module

RULES = "Write a short summary {not a format field}."


@pytest.fixture
def rules(tmp_path):
    path = tmp_path / "rules.md"
    path.write_text(RULES, encoding="utf-8")
    return path


def test_summarize_writes_documents_and_returns_summary(tmp_path, rules):
    launcher = FakeLauncher(writes("Итог"))
    pool = AIPool(launcher, rules)
    seen = []

    result = pool.summarize(["Первый", "", "Третий"], tmp_path / "out", on_run_dir=seen.append)

    run_dir = (tmp_path / "out" / "1").resolve()
    assert (result.summary, result.run_dir) == ("Итог", run_dir)
    assert seen == [run_dir]
    texts = [(run_dir / f"document-{n}.txt").read_text(encoding="utf-8") for n in (1, 2, 3)]
    assert texts == ["Первый", "", "Третий"]
    assert (run_dir / "summary.md").is_file()
    [(_, prompt)] = launcher.calls
    assert RULES in prompt and (run_dir / "summary.md").as_posix() in prompt
    positions = [prompt.index((run_dir / f"document-{n}.txt").as_posix()) for n in (1, 2, 3)]
    assert positions == sorted(positions)
    assert pool.summarize(["x"], tmp_path / "out").run_dir == run_dir.parent / "2"


def test_run_dir_number_follows_largest_numeric_dir(tmp_path, rules):
    out = tmp_path / "out"
    for name in ("1", "7", "x"):
        (out / name).mkdir(parents=True)
    (out / "3.txt").write_text("", encoding="utf-8")

    result = AIPool(FakeLauncher(writes("s")), rules).summarize(["a"], out)

    assert result.run_dir.name == "8"


def _raise_run_error(run_dir):
    raise AgentRunError("run status: error")


@pytest.mark.parametrize(
    ("behavior", "reason"),
    [(_raise_run_error, "run status: error"), (None, "not written"), (writes("  \n"), "empty")],
)
def test_agent_failure_keeps_run_dir(tmp_path, rules, behavior, reason):
    pool = AIPool(FakeLauncher(behavior), rules)

    with pytest.raises(SummaryError, match=reason):
        pool.summarize(["a"], tmp_path / "out")

    assert (tmp_path / "out" / "1" / "document-1.txt").is_file()


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("missing_key", MissingApiKeyError),
        ("bridge_fails", BridgeLaunchError),
        ("no_rules", RulesFileError),
        ("bad_rules", RulesFileError),
        ("output_is_file", RunDirError),
    ],
)
def test_start_failure_leaves_no_run_dir(tmp_path, rules, case, error):
    launcher = FakeLauncher(
        writes("s"), missing_key=case == "missing_key", bridge_fails=case == "bridge_fails"
    )
    out = tmp_path / "out"
    if case == "no_rules":
        rules.unlink()
    if case == "bad_rules":
        rules.write_bytes(b"\xff\xfe\x00")
    if case == "output_is_file":
        out.write_text("", encoding="utf-8")

    with pytest.raises(PoolError) as caught:
        AIPool(launcher, rules).summarize(["a"], out)

    assert isinstance(caught.value, error)
    if error is RulesFileError:
        assert str(rules) in str(caught.value)
    assert not (out / "1").exists()
    assert launcher.calls == []


def test_empty_document_list_is_rejected(tmp_path, rules):
    with pytest.raises(ValueError):
        AIPool(FakeLauncher(), rules).summarize([], tmp_path / "out")


def test_cursor_launcher_adapter(tmp_path, monkeypatch):
    calls, outcomes = [], iter(["finished", "error", CursorAgentError("boom", request_id="r1")])

    def prompt(prompt, options, client):
        calls.append(options)
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(id="r", status=outcome)

    bridge = SimpleNamespace(launch_bridge=lambda workspace: contextlib.nullcontext("client"))
    monkeypatch.setattr(launcher_module, "CursorClient", bridge)
    monkeypatch.setattr(session_module, "Agent", SimpleNamespace(prompt=prompt))
    monkeypatch.setenv("CURSOR_API_KEY", "key")
    launcher = CursorAgentLauncher("model")

    with launcher.connect(tmp_path) as session:
        session.prompt("p")
        with pytest.raises(AgentRunError, match="^run status: error$"):
            session.prompt("p")
        with pytest.raises(AgentRunError, match="^prompt failed: CursorAgentError"):
            session.prompt("p")
    options = calls[0]
    assert (options.model, options.api_key, options.local.cwd) == ("model", "key", str(tmp_path))
    assert options.agent_id.startswith("agent-") and options.agent_id != calls[1].agent_id
    monkeypatch.setenv("CURSOR_API_KEY", " ")
    with pytest.raises(MissingApiKeyError):
        launcher.check()
