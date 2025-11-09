"""
Logging configuration and utilities for DS-STAR.

Provides structured logging with multiple outputs:
- Console output with color coding
- File output with detailed information
- Real-time activity tracking for UI display
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock


class LogLevel(Enum):
    """Log levels for DS-STAR operations."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ActivityType(Enum):
    """Types of activities that can be logged."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    STATE_TRANSITION = "state_transition"
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    SERVICE_START = "service_start"
    SERVICE_END = "service_end"
    ERROR = "error"
    DEBUG_ATTEMPT = "debug_attempt"


class Activity:
    """Represents a single logged activity."""

    def __init__(
        self,
        activity_type: ActivityType,
        message: str,
        agent_name: Optional[str] = None,
        node_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.activity_type = activity_type
        self.message = message
        self.agent_name = agent_name
        self.node_name = node_name
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()

    def __str__(self) -> str:
        parts = [f"[{self.timestamp.strftime('%H:%M:%S')}]"]

        if self.agent_name:
            parts.append(f"[{self.agent_name}]")
        if self.node_name:
            parts.append(f"[{self.node_name}]")

        parts.append(self.message)

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary for structured logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.activity_type.value,
            "message": self.message,
            "agent_name": self.agent_name,
            "node_name": self.node_name,
            "details": self.details,
        }


class ActivityTracker:
    """
    Tracks activities in real-time for display in the UI.
    Thread-safe singleton that stores recent activities.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.activities: List[Activity] = []
        self.max_activities = 1000
        self.current_agent: Optional[str] = None
        self.current_node: Optional[str] = None
        self.iteration_count = 0
        self._initialized = True

    def log_activity(self, activity: Activity):
        """Add an activity to the tracker."""
        with self._lock:
            self.activities.append(activity)

            # Trim old activities if we exceed max
            if len(self.activities) > self.max_activities:
                self.activities = self.activities[-self.max_activities:]

            # Update current state
            if activity.agent_name:
                self.current_agent = activity.agent_name
            if activity.node_name:
                self.current_node = activity.node_name

    def get_recent(self, n: int = 10) -> List[Activity]:
        """Get the most recent n activities."""
        with self._lock:
            return self.activities[-n:]

    def get_all(self) -> List[Activity]:
        """Get all activities."""
        with self._lock:
            return list(self.activities)

    def get_by_type(self, activity_type: ActivityType) -> List[Activity]:
        """Get all activities of a specific type."""
        with self._lock:
            return [a for a in self.activities if a.activity_type == activity_type]

    def get_current_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        with self._lock:
            return {
                "current_agent": self.current_agent,
                "current_node": self.current_node,
                "iteration": self.iteration_count,
                "total_activities": len(self.activities),
            }

    def increment_iteration(self):
        """Increment the iteration counter."""
        with self._lock:
            self.iteration_count += 1

    def reset(self):
        """Reset the activity tracker."""
        with self._lock:
            self.activities.clear()
            self.current_agent = None
            self.current_node = None
            self.iteration_count = 0

    def clear(self):
        """Clear all activities."""
        with self._lock:
            self.activities.clear()


class DSStarLogger:
    """
    Custom logger for DS-STAR that integrates with both Python logging
    and the activity tracker.
    """

    def __init__(
        self,
        name: str,
        log_level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        console_output: bool = True,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level.value)
        self.logger.handlers.clear()

        self.activity_tracker = ActivityTracker()

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level.value)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _log_and_track(
        self,
        level: int,
        message: str,
        activity_type: ActivityType,
        agent_name: Optional[str] = None,
        node_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log a message and track it as an activity."""
        # Standard logging
        self.logger.log(level, message)

        # Activity tracking
        activity = Activity(
            activity_type=activity_type,
            message=message,
            agent_name=agent_name,
            node_name=node_name,
            details=details,
        )
        self.activity_tracker.log_activity(activity)

    def agent_start(self, agent_name: str, details: Optional[Dict[str, Any]] = None):
        """Log the start of an agent invocation."""
        message = f"Agent '{agent_name}' started"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.AGENT_START,
            agent_name=agent_name,
            details=details,
        )

    def agent_end(self, agent_name: str, details: Optional[Dict[str, Any]] = None):
        """Log the end of an agent invocation."""
        message = f"Agent '{agent_name}' completed"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.AGENT_END,
            agent_name=agent_name,
            details=details,
        )

    def state_transition(self, node_name: str, details: Optional[Dict[str, Any]] = None):
        """Log a state transition in the graph."""
        message = f"Entering node '{node_name}'"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.STATE_TRANSITION,
            node_name=node_name,
            details=details,
        )

    def execution_start(self, details: Optional[Dict[str, Any]] = None):
        """Log the start of code execution."""
        message = "Starting code execution"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.EXECUTION_START,
            details=details,
        )

    def execution_end(self, success: bool, details: Optional[Dict[str, Any]] = None):
        """Log the end of code execution."""
        status = "succeeded" if success else "failed"
        message = f"Code execution {status}"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.EXECUTION_END,
            details=details,
        )

    def llm_call_start(self, agent_name: str, details: Optional[Dict[str, Any]] = None):
        """Log the start of an LLM call."""
        message = f"LLM call started for '{agent_name}'"
        self._log_and_track(
            logging.DEBUG,
            message,
            ActivityType.LLM_CALL_START,
            agent_name=agent_name,
            details=details,
        )

    def llm_call_end(self, agent_name: str, details: Optional[Dict[str, Any]] = None):
        """Log the end of an LLM call."""
        message = f"LLM call completed for '{agent_name}'"
        self._log_and_track(
            logging.DEBUG,
            message,
            ActivityType.LLM_CALL_END,
            agent_name=agent_name,
            details=details,
        )

    def service_start(self, service_name: str, method: str, details: Optional[Dict[str, Any]] = None):
        """Log the start of a service method."""
        message = f"Service '{service_name}.{method}' started"
        self._log_and_track(
            logging.DEBUG,
            message,
            ActivityType.SERVICE_START,
            details=details,
        )

    def service_end(self, service_name: str, method: str, details: Optional[Dict[str, Any]] = None):
        """Log the end of a service method."""
        message = f"Service '{service_name}.{method}' completed"
        self._log_and_track(
            logging.DEBUG,
            message,
            ActivityType.SERVICE_END,
            details=details,
        )

    def error(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log an error."""
        self._log_and_track(
            logging.ERROR,
            message,
            ActivityType.ERROR,
            details=details,
        )

    def debug_attempt(self, attempt: int, max_attempts: int, details: Optional[Dict[str, Any]] = None):
        """Log a debug attempt."""
        message = f"Debug attempt {attempt}/{max_attempts}"
        self._log_and_track(
            logging.INFO,
            message,
            ActivityType.DEBUG_ATTEMPT,
            details=details,
        )

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)


def setup_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
) -> DSStarLogger:
    """
    Set up logging for DS-STAR.

    Args:
        log_level: Minimum log level to display
        log_file: Optional file path for logging
        console_output: Whether to output to console

    Returns:
        Configured DSStarLogger instance
    """
    return DSStarLogger(
        name="ds_star",
        log_level=log_level,
        log_file=log_file,
        console_output=console_output,
    )


def get_activity_tracker() -> ActivityTracker:
    """Get the global activity tracker instance."""
    return ActivityTracker()
