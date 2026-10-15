from typing import Protocol


class AgentSession(Protocol):
    """Connection to the agent backend of one run."""

    def prompt(self, prompt: str) -> None:
        """
        Run a new agent on the prompt in the run dir and wait until its run ends.

        :param prompt: summary prompt

        :raises AgentRunError: when the run fails or does not finish; the
            message is the reason
        """
        ...
