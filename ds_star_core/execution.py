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

    def __init__(self, settings: Optional[ExecutionSettings] = None, logger=None):
        self._settings = settings or ExecutionSettings()
        self.logger = logger

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

        if self.logger:
            self.logger.execution_start(details={
                "code_length": len(code),
                "timeout": effective_timeout
            })

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
                    exec_result = ExecutionResult(success=True, output=result.stdout)
                    if self.logger:
                        self.logger.execution_end(True, details={
                            "output_length": len(result.stdout),
                            "return_code": result.returncode
                        })
                    return exec_result

                exec_result = ExecutionResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr,
                    traceback=result.stderr,
                )
                if self.logger:
                    self.logger.execution_end(False, details={
                        "error": result.stderr[:200],
                        "return_code": result.returncode
                    })
                return exec_result
            finally:
                os.unlink(temp_file)
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.error(f"Execution timeout after {effective_timeout}s", details={
                    "timeout": effective_timeout
                })
            return ExecutionResult(
                success=False,
                output="",
                error="Execution timeout",
                traceback="Script execution exceeded timeout limit",
            )
        except Exception as exc:  # pylint: disable=broad-except
            if self.logger:
                self.logger.error(f"Execution error: {str(exc)}", details={
                    "exception": str(exc),
                    "traceback": traceback.format_exc()
                })
            return ExecutionResult(
                success=False,
                output="",
                error=str(exc),
                traceback=traceback.format_exc(),
            )

