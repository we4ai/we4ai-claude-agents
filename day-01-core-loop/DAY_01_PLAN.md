# Day 01: Core Agent Execution Loop, Streaming & Deterministic Control

**Target:** Claude Agent SDK (Python)  
**Deliverable Module:** `day-01-core-loop/`  
**Author:** GeekyRahul (@we4ai)  
**Status:** In Progress  

---

## 1. Executive Summary & Objective

The objective of Day 01 is to transition from basic `query()` calls to building a production-grade, deterministic execution runtime with the Claude Agent SDK. 

By the end of this module, the agent runtime will:
1. Handle the full message lifecycle (`AssistantMessage`, `StreamEvent`, `ToolUseBlock`, `ToolResultBlock`, `ResultMessage`).
2. Stream real-time thoughts and tokens with zero console buffering.
3. Enforce deterministic budget safeguards (`max_budget_usd`, `max_turns`) to prevent runaway execution loops.
4. Provide structured telemetry (token consumption, duration, and financial cost).
5. Pass adversarial stress tests designed to induce infinite loops.

---

## 2. Phased Execution Roadmap

```
┌──────────────────────────────────────────────────────────────┐
│ Phase 1: Baseline Architecture & Authentication (COMPLETED)  │
│ - Verified custom proxy endpoint (claude.vocareum.com)       │
│ - Configured .env loader and Windows UTF-8 stdout formatting  │
│ - Verified Read/Edit tool loops in agent.py                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 2: Real-time Streaming & Event Introspection           │
│ - ClaudeSDKClient vs query() streaming modes                 │
│ - Interactive streaming terminal UI (StreamEvent parsing)    │
│ - Visual separation: Thoughts vs Tool Calls vs Tool Outputs   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3: Deterministic Financial & Turn Safeguards           │
│ - Implement strict max_budget_usd & max_turns bounding      │
│ - Parse and log ResultMessage telemetry metadata             │
│ - Handle graceful degradation on error_max_budget_usd        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 4: Adversarial Stress Testing (Break The Agent)        │
│ - Build tests/test_bounds.py                                 │
│ - Induce circular tool dependency & contradictory prompts    │
│ - Assert hard termination within bounds                      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 5: Synthesis, Documentation & PR Submission            │
│ - Write architecture reflection & learnings journal          │
│ - Clean code formatting and typing assertions                │
│ - Squash & Merge to origin/main                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Work Breakdown & Tasks

### Task 1.1: Core Streaming Terminal Runner (`stream_runner.py`)
- **Action:** Implement an interactive CLI runner using `include_partial_messages=True`.
- **Requirements:**
  - Parse `StreamEvent` deltas for real-time word-by-word streaming.
  - Distinguish between assistant thinking text, tool calls, and tool returns.
  - Render visually distinct terminal blocks (e.g. `[THOUGHT]`, `[TOOL_USE: <name>]`, `[TOOL_RESULT]`).

### Task 1.2: Cost & Resource Guardrails (`bounded_agent.py`)
- **Action:** Build a reusable agent invocation wrapper that accepts strict operational thresholds.
- **Requirements:**
  - Accepts `max_budget_usd: float` (default: `$0.05`).
  - Accepts `max_turns: int` (default: `5`).
  - Extracts and formats `ResultMessage` metrics:
    - `total_cost_usd`
    - `duration_ms`
    - `num_turns`
    - Token counts (`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`).
  - Implements custom exit handlers for budget and turn limits.

### Task 1.3: Adversarial Boundary Test Suite (`tests/test_bounds.py`)
- **Action:** Create automated validation scripts using `pytest`.
- **Test Scenarios:**
  1. **Turn Cap Enforcement:** Prompt the agent with an impossible cyclic task. Assert it halts at exactly `max_turns` without hanging.
  2. **Budget Cap Enforcement:** Configure a micro-budget (`$0.0001`) and run a multi-step task. Assert termination with `subtype == "error_max_budget_usd"`.
  3. **Output Integrity:** Verify valid `ResultMessage` is always produced regardless of whether the run succeeded or hit limits.

### Task 1.4: Documentation & Knowledge Capture (`README.md` & `JOURNAL.md`)
- **Action:** Document the inner workings of the SDK execution cycle.
- **Key Concepts to Explain:**
  - Why `query()` operates as a unidirectional stream over NDJSON IPC.
  - The anatomy of the bundled `claude.exe` CLI process.
  - Stderr capture via `options.stderr` callback.
  - Differences between `query()` and `ClaudeSDKClient`.

---

## 4. Acceptance Criteria (AC) Status

| ID | Criteria | Status | Artifact / Script |
|---|---|:---:|---|
| **AC-01** | Real-time text streams token-by-token to stdout without batch delays. | ✅ **DONE** | `streamingAgent.py`, `basics.ipynb`, `01_AC01_STREAMING_TUTORIAL.md` |
| **AC-02** | Tool calls print tool name and serialized JSON arguments clearly. | ✅ **DONE** | `tooluseBlock.py`, `02_AC02_TOOL_CALL_INTROSPECTION_TUTORIAL.md` |
| **AC-03** | When `max_turns=N` is reached, agent halts cleanly and handles `error_max_turns`. | ✅ **DONE** | `maxTurns.py`, `turnInspector.py`, `03_AC03_MAX_TURNS_TUTORIAL.md` |
| **AC-04** | When `max_budget_usd` is breached, execution halts immediately with `error_max_budget_usd`. | ✅ **DONE** | `maxBudget.py`, `04_AC04_MAX_BUDGET_USD_TUTORIAL.md` |
| **AC-05** | Final run summary displays: total cost ($), elapsed time (s), turn count, and token usage. | ✅ **DONE** | `telemetryDashboard.py`, `05_AC05_TELEMETRY_DASHBOARD_TUTORIAL.md` |

---

## 5. Definition of Done (DoD) - Day 01 Sign-Off

1. **Source Code & Core Deliverables:**
   - [x] Stream tokens in real time via `StreamEvent` deltas with zero buffering (`flush=True`).
   - [x] Catch and pretty-print `ToolUseBlock` with formatted JSON inputs.
   - [x] Turn counter deduplication using Anthropic `message_id`.
   - [x] Graceful `ResultError` boundary trapping for turn and budget limits.
   - [x] Production telemetry dashboard reporting duration, latency, cost, and tokens.
   - [x] Zero hardcoded secrets (loaded securely from `.env`).

2. **Documentation & Knowledge Base:**
   - [x] Complete set of 5 bilingual tutorial documents (AC-01 through AC-05) created in repository.
   - [x] Architecture tradeoff understood: Raw API vs Agent SDK prompt floor economics.

3. **Sprint Status:**
   - [x] Day 01 Sprint Goals 100% Achieved. Ready for EOD commit and PR merge.
