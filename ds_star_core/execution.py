from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from typing import Optional

from .models import ExecutionResult


@dataclass
class ExecutionSettings:
    """Configuration for executing Python scripts."""

    timeout: int = 30


class PythonScriptRunner:
    """Utility that executes ad-hoc Python scripts within a temporary file."""

    def __init__(self, settings: Optional[ExecutionSettings] = None):
        self._settings = settings or ExecutionSettings()

    def run(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Execute Python code and return the result.

        Parameters
        ----------
        code:
            Python source code to execute.
        timeout:
            Optional override for the execution timeout. Defaults to the value provided
            when constructing the runner.
        """
        effective_timeout = timeout or self._settings.timeout

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as handle:
                handle.write(code)
                temp_file = handle.name

            try:
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                )

                if result.returncode == 0:
                    return ExecutionResult(success=True, output=result.stdout)

                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    traceback=result.stderr,
                )
            finally:
                os.unlink(temp_file)
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error="Execution timeout",
                traceback="Script execution exceeded timeout limit",
            )
        except Exception as exc:  # pylint: disable=broad-except
            return ExecutionResult(
                success=False,
                output="",
                error=str(exc),
                traceback=traceback.format_exc(),
            )

