# 🚀 Day 01: Core Agent Execution Loop, Streaming & Deterministic Control

> **Sprint Timeline:** Day 01 of 07  
> **Ecosystem:** Claude Agent SDK (Python)  
> **Status:** ✅ Completed & Verified  

---

## 📖 Executive Summary

Day 01 establishes the foundational engineering mechanics of autonomous agent development. Rather than treating LLMs as conversational chatbots, this module focuses on **runtime execution loops**, **real-time token streaming**, **tool call introspection**, **deterministic financial/turn guardrails**, and **structured telemetry observability**.

---

## 🗂️ Module Architecture & Directory Index

```
day-01-core-loop/
│
├── 📋 SPRINT SPECIFICATION
│   ├── README.md                          # Master Day 01 Module Overview
│   └── DAY_01_PLAN.md                     # Phased Roadmap, Acceptance Criteria & DoD
│
├── 📚 tutorials/                          # Master Architectural Guides (AC-01 to AC-05)
│   ├── 01_AC01_STREAMING_TUTORIAL.md      # Real-Time Token Streaming & Buffer Bypassing
│   ├── 02_AC02_TOOL_CALL_INTROSPECTION.md # ToolUseBlock Mechanics & Formatted Input Logging
│   ├── 03_AC03_MAX_TURNS_TUTORIAL.md      # Loop Bounds, Deduplication & error_max_turns
│   ├── 04_AC04_MAX_BUDGET_USD_TUTORIAL.md # Financial Safeguards, Prompt Floor & Cost Ceilings
│   └── 05_AC05_TELEMETRY_DASHBOARD.md     # Observability, Latency Breakdown & Token Metrics
│
├── 🔬 labs/                               # Hands-On AC Laboratory Scripts
│   ├── streamingAgent.py                  # AC-01: Real-time token streaming
│   ├── tooluseBlock.py                    # AC-02: Tool invocation & argument pretty-printer
│   ├── maxTurns.py                        # AC-03: Hard turn ceiling enforcement
│   ├── turnInspector.py                   # AC-03: Turn deduplication using API message_ids
│   ├── maxBudget.py                       # AC-04: Micro-budget ceiling & ResultError handling
│   ├── telemetryDashboard.py              # AC-05: Enterprise run telemetry visualizer
│   ├── test_bounds.py                     # Automated Pytest suite for boundary limits
│   └── agent.py                           # Baseline file repair agent
│
└── 🏗️ projects/                            # Enterprise Production Mini-Projects
    │
    ├── project-01-code-sentinel/          # Shift-Left Bug & Vulnerability Auditor
    │   ├── PRD.md                         # Product Requirements (Blast-Radius & Dynamic Sizing)
    │   ├── FSD.md                         # Functional Specification (State Machine & Findings Schema)
    │   ├── ARCHITECTURE.md                # C4 Context/Container Diagrams & ADRs
    │   └── sentinel.py                    # Production Runner with Dynamic Tiered Budgeting
    │
    └── project-02-docsync-auditor/        # Code-to-Documentation Parity Engine
        ├── PRD.md                         # Product Requirements (Documentation Drift)
        ├── FSD.md                         # Functional Specification & Discovery Algorithms
        ├── ARCHITECTURE.md                # C4 Models & Read-Only Governance ADRs
        └── auditor.py                     # Production Runner with Doc/Code Pairwise Sizing
```

---

## 🎯 Acceptance Criteria (AC) Verification Matrix

| ID | Engineering Acceptance Criteria | Verification Lab Script | Status |
|:---:|---|---|:---:|
| **AC-01** | Real-time text streams token-by-token with zero console buffering (`flush=True`). | [`labs/streamingAgent.py`](labs/streamingAgent.py) | ✅ **PASSED** |
| **AC-02** | Tool calls clearly print tool name (`Read`, `Glob`) and formatted JSON arguments. | [`labs/tooluseBlock.py`](labs/tooluseBlock.py) | ✅ **PASSED** |
| **AC-03** | When `max_turns=N` is hit, agent terminates cleanly without hanging; handles `error_max_turns`. | [`labs/turnInspector.py`](labs/turnInspector.py) | ✅ **PASSED** |
| **AC-04** | When `max_budget_usd` is breached, execution halts immediately with `error_max_budget_usd`. | [`labs/maxBudget.py`](labs/maxBudget.py) | ✅ **PASSED** |
| **AC-05** | Final run summary displays Total Duration, API Latency, Turns, Cost ($), and Token usage. | [`labs/telemetryDashboard.py`](labs/telemetryDashboard.py) | ✅ **PASSED** |

---

## 🏗️ Enterprise Mini-Projects Showcase

### 1. 🛡️ Autonomous Code Sentinel
- **Goal:** Shift-left pre-commit security and runtime crash bug auditor.
- **Enterprise Sizing:** Implements **Dynamic Tiered Budgeting** scaling across Micro (Tier 1: 6 turns, $0.10), Standard PR (Tier 2: 15 turns, $0.40), and Subsystem (Tier 3: 25 turns, $1.50).
- **Architecture Spec:** [projects/project-01-code-sentinel/ARCHITECTURE.md](projects/project-01-code-sentinel/ARCHITECTURE.md)
- **Run:**
  ```powershell
  python day-01-core-loop/projects/project-01-code-sentinel/sentinel.py
  ```

### 2. 📚 DocSync Auditor
- **Goal:** Autonomous detection of documentation drift against live code function signatures.
- **Enterprise Sizing:** Dynamically scales turns (8 to 30) and budget ($0.15 to $2.00) based on repository doc/code density.
- **Architecture Spec:** [projects/project-02-docsync-auditor/ARCHITECTURE.md](projects/project-02-docsync-auditor/ARCHITECTURE.md)
- **Run:**
  ```powershell
  python day-01-core-loop/projects/project-02-docsync-auditor/auditor.py
  ```

---

## 💡 Key Architectural Insights Uncovered

1. **The "Prompt Floor" Cost Phenomenon:**  
   The first API call of an agent includes the Claude Code system prompt (~1,500 tokens) and built-in tool schemas (~2,500 tokens). A single turn incurs a baseline cost (~$0.0028 on Sonnet, ~$0.0009 on Haiku), regardless of prompt size.
2. **API Duration vs Wall-Clock Duration:**  
   `duration_api_ms` can exceed `duration_ms` when the underlying CLI runs asynchronous sub-tasks or background validations concurrently.
3. **Turn Deduplication:**  
   An agent turn may emit multiple intermediate `AssistantMessage` events. True turn boundaries are tracked by deduplicating unique Anthropic `message_id`s.
4. **Boundary Interception via `ResultError`:**  
   When `max_turns` or `max_budget_usd` is reached, the CLI exits with non-zero status. The Python SDK converts this into a typed `ResultError`, enabling graceful enterprise error trapping.

---

## 🧪 Running the Automated Test Suite

```powershell
# Run the automated bounds test suite
pytest day-01-core-loop/test_bounds.py -v
```

---

*Authored by the WE4AI Autonomous Engineering Team (@we4ai)*
