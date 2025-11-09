# DS-STAR Logging and Real-Time Activity Tracking

DS-STAR now includes comprehensive logging and real-time activity tracking to help you understand what the agents are doing during execution.

## Features

### 1. **Real-Time Activity Tracking**

Watch agent activities as they happen during execution. The system tracks:
- Agent invocations (start/end)
- State transitions in the execution graph
- Code execution (start/end, success/failure)
- LLM API calls
- Error events
- Debug attempts

### 2. **Configurable Logging**

When you run DS-STAR, you'll be prompted to configure logging:

```
Log level options: DEBUG, INFO, WARNING, ERROR
Log level [INFO]:
```

**Log Levels:**
- `DEBUG`: Detailed information including all LLM calls and internal operations
- `INFO`: General information about agent activities and state transitions (default)
- `WARNING`: Only warnings and errors
- `ERROR`: Only errors

### 3. **Log File Output**

Optionally save logs to a file for later analysis:

```
Save logs to file? (optional)
Log file path (or press Enter to skip): ds_star.log
```

### 4. **Real-Time Display**

Enable real-time activity display to see what's happening as it happens:

```
Display real-time agent activity?
Enable real-time display? [Y/n]:
```

When enabled, you'll see live updates like:
```
[14:32:15] 🤖 AGENT: Agent 'AnalyzerAgent' started
[14:32:16] 🔄 STATE: Entering node 'analyze'
[14:32:18] ▶️  EXEC: Starting code execution
[14:32:19] ✅ DONE: Code execution succeeded
```

## Activity Types

The system tracks different types of activities with visual indicators:

| Icon | Type | Description |
|------|------|-------------|
| 🤖 | AGENT | Agent invocation |
| 🔄 | STATE | State transition in the execution graph |
| ▶️ | EXEC | Code execution started |
| ✅ | DONE | Successful completion |
| ❌ | ERROR/FAIL | Error or failure |
| 🔧 | DEBUG | Debug attempt |
| ℹ️ | INFO | General information |

## Execution Summary

After execution completes, you'll see a summary of all activities:

```
========================================================================
                          EXECUTION SUMMARY
========================================================================

Agent Activity:
  Total agent calls: 15
  Completed calls: 15
  Errors: 0

  Agent usage:
    AnalyzerAgent: 3
    CoderAgent: 4
    PlannerAgent: 4
    VerifierAgent: 3
    RouterAgent: 1

Code Execution:
  Total executions: 5
  Successful: 4
  Failed: 1

Total iterations: 3
Total activities logged: 45
```

## Viewing Activity Logs

After execution, you can view detailed activity logs:

```
View detailed activity log? [y/N]: y

Recent Activities (last 50):
------------------------------------------------------------------------
[14:32:15] [AnalyzerAgent] Agent 'AnalyzerAgent' started
[14:32:15] [analyze] Entering node 'analyze'
[14:32:18] [AnalyzerAgent] Agent 'AnalyzerAgent' completed
...
```

## Programmatic Access

You can also access activity tracking programmatically:

```python
from ds_star_core.logging_config import get_activity_tracker
from ds_star_core.tui import ActivitySummary

# Get the activity tracker
tracker = get_activity_tracker()

# Get current status
status = tracker.get_current_status()
print(f"Current agent: {status['current_agent']}")
print(f"Current iteration: {status['iteration']}")

# Get recent activities
recent = tracker.get_recent(10)
for activity in recent:
    print(activity)

# Get activity summary
summary = ActivitySummary()
summary.print_summary()
```

## Architecture

### Components

1. **DSStarLogger** (`ds_star_core/logging_config.py`)
   - Handles structured logging with Python's logging module
   - Integrates with the ActivityTracker

2. **ActivityTracker** (`ds_star_core/logging_config.py`)
   - Thread-safe singleton that stores activities
   - Tracks current execution state
   - Provides query methods for activities

3. **TUI Components** (`ds_star_core/tui.py`)
   - `RealTimeActivityDisplay`: Live activity updates
   - `StatusLine`: Current execution status
   - `ActivitySummary`: Summary statistics

### Activity Flow

```
Agent/Service/Execution
        ↓
   DSStarLogger
        ↓
  ActivityTracker (singleton)
        ↓
   TUI Display Components
        ↓
   Console Output
```

## Configuration Options

When initializing DSSTAR programmatically:

```python
from ds_star import DSSTAR
from llm_clients import GeminiClient

llm_client = GeminiClient()
ds_star = DSSTAR(
    llm_client=llm_client,
    log_level="INFO",           # Log level: DEBUG, INFO, WARNING, ERROR
    log_file="ds_star.log",     # Optional log file path
    enable_logging=True,        # Enable/disable logging
    verbose=True,               # Show console output
)
```

## Benefits

1. **Transparency**: See exactly what each agent is doing
2. **Debugging**: Easily identify where issues occur
3. **Performance**: Track execution times and iteration counts
4. **Analysis**: Review logs to understand the solution process
5. **User Control**: Configure logging based on your needs

## Example Session

```
========================================================================
                   DS-STAR Interactive Console
========================================================================

------------------------------------------------------------------------
                         LOGGING OPTIONS
------------------------------------------------------------------------
Configure logging and real-time activity tracking.

Log level options: DEBUG, INFO, WARNING, ERROR
Log level [INFO]: INFO

Save logs to file? (optional)
Log file path (or press Enter to skip): execution.log

Display real-time agent activity?
Enable real-time display? [Y/n]: y

------------------------------------------------------------------------
                      SELECT QUERY FILE
------------------------------------------------------------------------
...
```

During execution:
```
------------------------------------------------------------------------
                           SOLVING
------------------------------------------------------------------------
Submitting your request to DS-STAR...

📊 Real-time activity tracking enabled
Watch agent activities below:

[14:30:45] 🔄 STATE: Entering node 'analyze'
[14:30:45] 🤖 AGENT: Agent 'AnalyzerAgent' started
[14:30:47] 🤖 AGENT: Agent 'AnalyzerAgent' completed
[14:30:47] 🔄 STATE: Entering node 'planner_initial'
[14:30:47] 🤖 AGENT: Agent 'PlannerAgent' started
...
```

## Tips

- Use `DEBUG` level when troubleshooting specific issues
- Use `INFO` level for normal operation with visibility
- Use `WARNING` or `ERROR` when you only want to see problems
- Save logs to a file for later analysis or debugging
- Enable real-time display to watch the solution process unfold
