# 📐 Functional Specification Document (FSD)
## Autonomous Code Sentinel

---

## 1. Dynamic Budgeting & Sizing Algorithm

Before initiating the autonomous agent loop, the runner executes a pre-flight discovery pass to calculate the appropriate budget tier:

```python
def calculate_dynamic_budget(target_files: list[str]) -> tuple[int, float]:
    """
    Computes (max_turns, max_budget_usd) based on candidate audit footprint.
    """
    count = len(target_files)
    
    # Tier 1: Micro Audit (1-2 files)
    if count <= 2:
        return (6, 0.10)
    
    # Tier 2: Standard Module / Feature Diff (3-10 files)
    elif count <= 10:
        return (15, 0.40)
        
    # Tier 3: Subsystem / Architectural Review (> 10 files)
    else:
        # Cap at 25 turns and $1.50 ceiling for single-agent runs
        return (25, 1.50)
```

---

## 2. State Machine & Execution Flow

```
                      [START]
                         │
                         ▼
             [Pre-Flight: File Discovery]
           - Scan target pattern (e.g. *.py)
           - Compute Dynamic Tier:
             • Turns: 6 / 15 / 25
             • Budget: $0.10 / $0.40 / $1.50
                         │
                         ▼
            [Options Injection & Guardrails]
           - Inject max_turns & max_budget_usd
           - Allow tools: ["Read", "Glob"]
           - Model: claude-haiku-4-5-20251001
                         │
                         ▼
           [Autonomous ReAct Execution Loop]
           - Turn 1: Glob & Identify Candidate Entry Points
           - Turn 2..N: Read files, inspect functions, check types
           - Stream tokens live to stdout (StreamEvent)
           - Log tool calls with formatted JSON (ToolUseBlock)
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
 [Normal Completion]             [Boundary Triggered]
 - ResultMessage: success        - ResultError: error_max_turns / error_max_budget_usd
 - Telemetry: Cost, Turns        - Graceful recovery, partial findings reported
         └───────────────┬───────────────┘
                         ▼
             [Output Findings Scorecard]
                         │
                         ▼
                       [END]
```

---

## 3. Data Contracts & Output Schema

The agent is instructed to structure its final report in the following format:

### 🛡️ Sentinel Audit Findings

| Severity | File | Function / Location | Vulnerability Description | Suggested Surgical Fix |
|:---:|---|---|---|---|
| 🔴 CRITICAL | `testing.py` | `calculate_average` | `ZeroDivisionError` on empty list input. | Add `if not numbers: return 0.0`. |
| 🟠 WARNING  | `testing.py` | `get_user_name` | `KeyError` or non-dict `TypeError`. | Verify `isinstance(user, dict)` before indexing. |

