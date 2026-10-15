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

    assert main.run([str(env.folder), str(env.out)]) == 0

    assert capsys.readouterr().out == "Итоговое резюме\n"
    run_dir = env.out / "1"
    texts = [(run_dir / f"document-{n}.txt").read_text(encoding="utf-8") for n in (1, 2, 3)]
    assert texts == ["text of a.JPG", "text of b.pdf", "text of c.webp"]
    assert not (run_dir / "document-4.txt").exists()


@pytest.mark.parametrize("case", ["missing", "file", "only_txt", "corrupt_pdf", "no_key"])
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

    assert main.run([str(folder), str(env.out)]) == 1

    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert env.launcher.calls == []
    if case == "corrupt_pdf":
        assert "bad.pdf" in err
    if case == "no_key":
        assert env.read == []
