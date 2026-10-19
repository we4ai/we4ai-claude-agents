# 📄 Product Requirements Document (PRD)
## Autonomous Code Sentinel (Enterprise Pre-Commit Bug & Vulnerability Auditor)

**Product Status:** Approved for Implementation  
**Version:** 2.0 (Enterprise Scaled)  
**Target Runtime:** Claude Agent SDK (Python)  

---

## 1. Executive Summary & Vision
Autonomous Code Sentinel is a shift-left, pre-commit security and runtime bug detection agent. Traditional static linters check syntax and styling but miss runtime logic flaws (e.g., zero-division errors, unhandled `NoneType` propagation, resource leaks, and insecure parameter injection). Sentinel operates autonomously on local developer machines or CI/CD pre-commit runners to perform semantic audits on code before it merges into main branches.

---

## 2. Real-World Engineering Reality: The Sizing Problem
In a real enterprise monorepo or service codebase (50 to 500+ files):
- **Static Toy Limits Fail:** A static 3-turn limit or $0.03 budget fails immediately. Listing files alone consumes 1-2 turns; tracing imports across modules requires 8-15 turns.
- **Unbounded Runaway Loops Burn Money:** Without upper limits, an ambiguous prompt can enter circular retry loops, costing tens of dollars.
- **The Solution:** **Dynamic Tiered Budgeting & Blast-Radius Scoping**.

---

## 3. Scope & Blast-Radius Definition

Sentinel operates on **Staged Git Diffs and Targeted Blast Radii**, not the entire repository naively:
1. **Tier 1 (Micro Diff - 1 to 2 files changed):**
   - *Scope:* Single module fix or hotfix.
   - *Target Turns:* 6 turns.
   - *Financial Ceiling:* $0.10 USD.
2. **Tier 2 (Standard PR - 3 to 10 files changed):**
   - *Scope:* Feature PR touching interfaces, implementations, and tests.
   - *Target Turns:* 15 turns.
   - *Financial Ceiling:* $0.40 USD.
3. **Tier 3 (Subsystem Audit - 10+ files or cross-cutting refactor):**
   - *Scope:* Architectural refactor, major version migration.
   - *Target Turns:* 25 turns.
   - *Financial Ceiling:* $1.50 USD.

---

## 4. User Personas
- **Developer / Contributor:** Wants pre-commit feedback in under 30 seconds with zero manual configuration.
- **Security / Compliance Engineer:** Requires audit logs proving no unchecked vulnerabilities bypass review.
- **Engineering Manager:** Needs strict financial predictability across thousands of developer pre-commit hooks.

---

## 5. Functional Requirements (FR)
- **FR-01: Dynamic Budget Calculation:** Agent dynamically computes `max_turns` and `max_budget_usd` by inspecting the count and lines of code (LOC) of candidate files.
- **FR-02: Real-Time Stream Transparency:** Emits live token streaming (`StreamEvent`) and logs every tool invocation (`ToolUseBlock`) with formatted JSON parameters.
- **FR-03: Boundary Ceiling Interception:** If a scan reaches the budget or turn ceiling, it must halt cleanly with `ResultError` interception (Exit Code 0).
- **FR-04: Structured Vulnerability Scorecard:** Outputs findings categorized by severity (Critical / Warning / Info) with exact line references and suggested fixes.

---

## 6. Non-Functional Requirements (NFR)
- **Performance:** Time-to-first-token under 2.5 seconds on Haiku 4.5.
- **Platform Resilience:** Windows UTF-8 console safe (`cp1252` crash prevention).
- **Security:** Zero network transmission of uncommitted secrets or local env files (`.env` explicitly ignored).
