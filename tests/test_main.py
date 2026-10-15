from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import FakeLauncher, writes

from summary import main
from summary.ai_pool.cursor import CursorAgentLauncher
from summary.text_reader import UnsupportedFormatError, read_text

SUPPORTED = {".pdf", ".jpg", ".jpeg", ".webp"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Repo root as working dir, a fake ``read_text`` and a fake launcher."""
    monkeypatch.chdir(Path(__file__).parents[1])
    monkeypatch.setenv("CURSOR_API_KEY", "key")
    read = []

    def fake_read_text(path):
        path = Path(path)
        if path.suffix.lower() not in SUPPORTED:
            raise UnsupportedFormatError(path)
        read.append(path.name)
        return f"text of {path.name}"

    launcher = FakeLauncher(writes("Итоговое резюме"))
    monkeypatch.setattr(main, "read_text", fake_read_text)
    monkeypatch.setattr(main, "CursorAgentLauncher", lambda model: launcher)
    folder = tmp_path / "in"
    folder.mkdir()
    return SimpleNamespace(folder=folder, out=tmp_path / "out", launcher=launcher, read=read)


def touch(folder, *names):
    for name in names:
        (folder / name).write_bytes(b"not a document")


def test_summarizes_supported_top_level_files_in_name_order(env, capsys):
    touch(env.folder, "b.pdf", "a.JPG", "c.webp", "notes.txt")
    (env.folder / "d.pdf").mkdir()
    touch(env.folder / "d.pdf", "e.pdf")
    mid_run_logs = []

    def behavior(run_dir):
        mid_run_logs.append((run_dir / "run.log").read_text(encoding="utf-8"))
        writes("Итоговое резюме")(run_dir)

    env.launcher.behavior = behavior

    assert main.run([str(env.folder), str(env.out)]) == 0

    captured = capsys.readouterr()
    assert captured.out == "Итоговое резюме\n"
    run_dir = env.out / "1"
    texts = [(run_dir / f"document-{n}.txt").read_text(encoding="utf-8") for n in (1, 2, 3)]
    assert texts == ["text of a.JPG", "text of b.pdf", "text of c.webp"]
    assert not (run_dir / "document-4.txt").exists()
    run_log = (run_dir / "run.log").read_text(encoding="utf-8")
    assert "run started" in mid_run_logs[0] and "run dir created" in mid_run_logs[0]
    for record in ("read a.JPG", "skipped notes.txt", "run done"):
        assert record in run_log
    for record in ("run started", "read a.JPG", "skipped notes.txt", "run dir created", "run done"):
        assert f"INFO {record}" in captured.err
    for log in (run_log, captured.err):
        assert "text of" not in log and "Итоговое резюме" not in log


@pytest.mark.parametrize("flags", [[], ["-v"], ["-q"]])
def test_summary_error_is_logged(env, capsys, flags):
    touch(env.folder, "a.pdf")
    env.launcher.behavior = None

    assert main.run([*flags, str(env.folder), str(env.out)]) == 1

    err = capsys.readouterr().err
    run_log = (env.out / "1" / "run.log").read_text(encoding="utf-8")
    assert err.splitlines()[-1].startswith("error: ")
    assert "ERROR" in run_log and "Traceback" in run_log
    assert ("Traceback" in err) == (flags == ["-v"])
    assert ("INFO" in err) == (flags != ["-q"])


def test_verbose_and_quiet_conflict(env):
    with pytest.raises(SystemExit) as caught:
        main.run(["-v", "-q", str(env.folder), str(env.out)])
    assert caught.value.code == 2


@pytest.mark.parametrize(
    "case", ["missing", "file", "only_txt", "corrupt_pdf", "no_key", "bridge"]
)
def test_errors_exit_with_code_1(env, capsys, monkeypatch, case):
    folder = env.folder
    if case == "missing":
        folder = folder / "missing"
    if case == "file":
        folder = folder / "a.pdf"
        touch(env.folder, "a.pdf")
    if case == "only_txt":
        touch(folder, "notes.txt")
    if case == "corrupt_pdf":
        touch(folder, "bad.pdf")
        monkeypatch.setattr(main, "read_text", read_text)
    if case == "no_key":
        touch(folder, "a.pdf")
        monkeypatch.delenv("CURSOR_API_KEY")
        monkeypatch.setattr(main, "CursorAgentLauncher", CursorAgentLauncher)
    if case == "bridge":
        touch(folder, "a.pdf")
        env.launcher.bridge_fails = True

    assert main.run([str(folder), str(env.out)]) == 1

    err = capsys.readouterr().err
    assert err.splitlines()[-1].startswith("error: ")
    assert env.launcher.calls == []
    if case == "bridge":
        assert not (env.out / "1").exists()
    if case == "corrupt_pdf":
        assert "bad.pdf" in err
    if case == "no_key":
        assert env.read == []
