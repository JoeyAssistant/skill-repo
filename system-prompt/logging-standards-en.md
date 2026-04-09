## Logging Standards

When writing code, you MUST strictly follow the logging principles and format specifications below. Ensure logs are both human-readable and AI-parseable.

### Logging Principles

1. **Log all external calls**: Print request parameters before calling external modules/services; print return results and latency after the call
2. **Log key process nodes and state changes**: Business flow start/end, state machine transitions, task completion, and other critical nodes MUST be logged
3. **Log all errors and exceptions**: MUST include error code, error description, root cause clues
4. **Prevent log flooding**: Do NOT log per iteration in high-frequency loops. Do NOT log large binary data. For high-frequency calls (e.g., cache reads), do NOT log on normal success; only log on exceptions
5. **Prevent sensitive information leakage**: Do NOT output passwords, authentication credentials, encryption keys, tokens, or other sensitive information in logs

### Log Level Standards

Use log levels strictly according to the following definitions. Do NOT misuse levels:

**ERROR** — Errors that affect normal business function and require human intervention:
- External call failed with no automatic recovery (retries exhausted, connection permanently lost)
- Data consistency issues (write failure, validation failure)
- System-level exceptions (resource exhaustion)
- MUST include: error code, error description, root cause clues, related parameters

**WARN** — Abnormal but automatically recoverable; does not affect main flow:
- External call failed but will auto-retry
- Degradation/fallback activated
- Configuration missing, using default value
- Approaching threshold warnings
- MUST include: exception description, current state, recovery strategy

**INFO** — Key business process nodes and state changes for traceability:
- Service start/stop
- External call succeeded (with result summary and latency)
- Key business state changes (task start/completion, state machine transitions)
- Configuration loaded
- MUST include: event description, key parameters

**DEBUG** — Detailed information for development debugging; disabled by default in production:
- Function inputs/outputs
- Intermediate computation details
- Protocol/encode/decode details
- MUST include: detailed context variable values

**Level Usage Rules**:
- Retry scenarios: log WARN for each intermediate failure; log INFO on final success with retry count; log ERROR on final failure
- High-frequency calls: do NOT log on normal success; only log WARN/ERROR on exceptions

### Structured Log Format

Each log entry MUST consist of the following three parts in a consistent text format:

1. **Context TAG**: Select necessary TAG fields based on the actual project and business context. Not all fields are mandatory. Common fields include but are not limited to: timestamp, log level, module name, thread/coroutine ID, trace identifier (traceID/sessionID/taskID), class:function
2. **Text Description**: Concise English description of the event or error, e.g., `Connect to server failed`, `Task completed successfully`
3. **KV Parameters**: Detailed parameters in `key=value` format, comma-separated

**Format Template**:
```
[TAG1] [TAG2] ... [Class:Function] Text description, key1=value1, key2=value2
```

**Examples**:
```
[2026-04-07 10:23:45.678] [ERROR] [NetworkModule] [tid:1234] [traceID:abc-001] [ConnectionManager:connect] Connect to server failed, host=192.168.1.100, port=8080, errorCode=ETIMEDOUT, retryCount=3
[2026-04-07 10:23:46.100] [INFO] [NetworkModule] [tid:1234] [traceID:abc-001] [ConnectionManager:connect] Connect to server succeeded after retry, host=192.168.1.100, port=8080, retryCount=3, latency=422ms
```
