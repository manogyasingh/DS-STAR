"""
Terminal UI utilities for displaying real-time agent activity.
"""

import sys
import threading
import time
from typing import Optional

from .logging_config import ActivityTracker, ActivityType


class RealTimeActivityDisplay:
    """
    Displays real-time agent activity in the terminal.
    Runs in a separate thread to continuously update the display.
    """

    def __init__(self, console_width: int = 72):
        self.console_width = console_width
        self.tracker = ActivityTracker()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_displayed = 0

    def start(self):
        """Start the real-time display."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the real-time display."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _update_loop(self):
        """Main update loop that runs in a separate thread."""
        while self._running:
            self._display_updates()
            time.sleep(0.5)  # Update every 500ms

    def _display_updates(self):
        """Display new activities since last check."""
        activities = self.tracker.get_all()
        new_activities = activities[self._last_displayed:]

        for activity in new_activities:
            self._print_activity(activity)

        self._last_displayed = len(activities)

    def _print_activity(self, activity):
        """Print a single activity to the terminal."""
        # Color coding based on activity type
        if activity.activity_type == ActivityType.ERROR:
            prefix = "❌ ERROR"
        elif activity.activity_type == ActivityType.AGENT_START:
            prefix = "🤖 AGENT"
        elif activity.activity_type == ActivityType.EXECUTION_START:
            prefix = "▶️  EXEC"
        elif activity.activity_type == ActivityType.EXECUTION_END:
            prefix = "✅ DONE" if activity.details.get("success") else "❌ FAIL"
        elif activity.activity_type == ActivityType.STATE_TRANSITION:
            prefix = "🔄 STATE"
        elif activity.activity_type == ActivityType.DEBUG_ATTEMPT:
            prefix = "🔧 DEBUG"
        else:
            prefix = "ℹ️  INFO"

        # Format the message
        timestamp = activity.timestamp.strftime("%H:%M:%S")
        msg = f"[{timestamp}] {prefix}: {activity.message}"

        # Truncate if too long
        if len(msg) > self.console_width:
            msg = msg[:self.console_width - 3] + "..."

        print(msg)
        sys.stdout.flush()


class StatusLine:
    """
    Displays a persistent status line showing current execution state.
    """

    def __init__(self, console_width: int = 72):
        self.console_width = console_width
        self.tracker = ActivityTracker()

    def display(self):
        """Display the current status."""
        status = self.tracker.get_current_status()

        parts = []

        if status.get("current_node"):
            parts.append(f"Node: {status['current_node']}")

        if status.get("current_agent"):
            parts.append(f"Agent: {status['current_agent']}")

        iteration = status.get("iteration", 0)
        if iteration > 0:
            parts.append(f"Iteration: {iteration}")

        if not parts:
            parts.append("Idle")

        status_line = " | ".join(parts)

        # Center the status line
        print()
        print("=" * self.console_width)
        print(status_line.center(self.console_width))
        print("=" * self.console_width)
        print()
        sys.stdout.flush()

    def display_compact(self):
        """Display a compact status line."""
        status = self.tracker.get_current_status()

        parts = []
        if status.get("current_node"):
            parts.append(status["current_node"])
        if status.get("iteration", 0) > 0:
            parts.append(f"Iter {status['iteration']}")

        if parts:
            status_text = " | ".join(parts)
            print(f"[Status: {status_text}]")
            sys.stdout.flush()


class ActivitySummary:
    """
    Provides summary views of logged activities.
    """

    def __init__(self):
        self.tracker = ActivityTracker()

    def get_agent_summary(self):
        """Get a summary of agent activities."""
        activities = self.tracker.get_all()

        agent_starts = [a for a in activities if a.activity_type == ActivityType.AGENT_START]
        agent_ends = [a for a in activities if a.activity_type == ActivityType.AGENT_END]
        errors = [a for a in activities if a.activity_type == ActivityType.ERROR]

        agent_counts = {}
        for activity in agent_starts:
            agent_name = activity.agent_name
            if agent_name:
                agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1

        return {
            "total_agent_calls": len(agent_starts),
            "completed_agent_calls": len(agent_ends),
            "errors": len(errors),
            "agent_counts": agent_counts,
        }

    def get_execution_summary(self):
        """Get a summary of code executions."""
        activities = self.tracker.get_all()

        exec_starts = [a for a in activities if a.activity_type == ActivityType.EXECUTION_START]
        exec_ends = [a for a in activities if a.activity_type == ActivityType.EXECUTION_END]

        successful = sum(1 for a in exec_ends if a.details.get("success"))
        failed = sum(1 for a in exec_ends if not a.details.get("success"))

        return {
            "total_executions": len(exec_starts),
            "successful": successful,
            "failed": failed,
        }

    def print_summary(self):
        """Print a summary of all activities."""
        agent_summary = self.get_agent_summary()
        exec_summary = self.get_execution_summary()

        print()
        print("=" * 72)
        print("EXECUTION SUMMARY".center(72))
        print("=" * 72)
        print()

        print("Agent Activity:")
        print(f"  Total agent calls: {agent_summary['total_agent_calls']}")
        print(f"  Completed calls: {agent_summary['completed_agent_calls']}")
        print(f"  Errors: {agent_summary['errors']}")

        if agent_summary['agent_counts']:
            print()
            print("  Agent usage:")
            for agent, count in sorted(agent_summary['agent_counts'].items()):
                print(f"    {agent}: {count}")

        print()
        print("Code Execution:")
        print(f"  Total executions: {exec_summary['total_executions']}")
        print(f"  Successful: {exec_summary['successful']}")
        print(f"  Failed: {exec_summary['failed']}")

        status = self.tracker.get_current_status()
        print()
        print(f"Total iterations: {status.get('iteration', 0)}")
        print(f"Total activities logged: {status.get('total_activities', 0)}")
        print()


def print_recent_activities(n: int = 10):
    """Print the most recent activities."""
    tracker = ActivityTracker()
    activities = tracker.get_recent(n)

    if not activities:
        print("No activities logged yet.")
        return

    print()
    print(f"Recent Activities (last {min(n, len(activities))}):")
    print("-" * 72)

    for activity in activities:
        print(str(activity))

    print()
