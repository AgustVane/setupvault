from __future__ import annotations

import shlex
import subprocess
from collections.abc import Sequence
from typing import Any


class SafeCommandRunner:
    """Wrapper around ``subprocess`` that enforces safe execution.

    Every command is run with ``shell=False`` and args passed as a
    sequence, never a string. This prevents shell injection.
    """

    def __init__(self, timeout: float | None = 30.0) -> None:
        self._timeout = timeout

    def run(
        self,
        args: Sequence[str | Any],
        *,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: float | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a command safely.

        Args:
            args: Command and arguments as a sequence (never a string).
            check: If True, raise ``CalledProcessError`` on non-zero exit.
            capture_output: If True, capture stdout and stderr.
            text: If True, decode output as text (``universal_newlines``).
            timeout: Override the default timeout.
            env: Optional environment variables.

        Returns:
            ``subprocess.CompletedProcess`` instance.

        Raises:
            subprocess.CalledProcessError: If *check* is True and exit code != 0.
            subprocess.TimeoutExpired: If the command times out.
        """
        str_args = [str(a) for a in args]
        return subprocess.run(
            str_args,
            capture_output=capture_output,
            text=text,
            check=check,
            timeout=timeout or self._timeout,
            env=env,
        )

    def check_tool(self, name: str) -> bool:
        """Check whether a tool is available on ``$PATH``."""
        try:
            self.run(["which", name], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_output(self, args: Sequence[str | Any], **kwargs: Any) -> str:
        """Run a command and return its stdout as a stripped string."""
        result = self.run(args, capture_output=True, text=True, **kwargs)
        out = result.stdout
        assert isinstance(out, str)
        return out.strip()


def format_command(args: Sequence[str | Any]) -> str:
    """Format a command sequence for display (safe, shell-escaped)."""
    return " ".join(shlex.quote(str(a)) for a in args)
