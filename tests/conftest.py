import contextlib

from summary.ai_pool import BridgeLaunchError, MissingApiKeyError


class FakeLauncher:
    """Agent launcher whose session runs ``behavior(run_dir)`` instead of an agent."""

    def __init__(self, behavior=None, missing_key=False, bridge_fails=False):
        self.behavior = behavior
        self.missing_key = missing_key
        self.bridge_fails = bridge_fails
        self.calls = []

    def check(self):
        if self.missing_key:
            raise MissingApiKeyError("CURSOR_API_KEY is not set")

    @contextlib.contextmanager
    def connect(self, run_dir):
        if self.bridge_fails:
            raise BridgeLaunchError("cannot launch bridge")
        yield FakeSession(self, run_dir)


class FakeSession:
    def __init__(self, launcher, run_dir):
        self.launcher = launcher
        self.run_dir = run_dir

    def prompt(self, prompt):
        self.launcher.calls.append((self.run_dir, prompt))
        if self.launcher.behavior:
            self.launcher.behavior(self.run_dir)


def writes(text):
    """Behaviour that writes ``text`` to the summary file of the run dir."""
    return lambda run_dir: (run_dir / "summary.md").write_text(text, encoding="utf-8")
