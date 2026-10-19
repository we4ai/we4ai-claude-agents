# 🏛️ System Architecture & Design
## Autonomous Code Sentinel

---

## 1. C4 Architecture Models

### 1.1 Level 1: System Context Diagram

```mermaid
graph TD
    User[Developer / CI Runner] -->|Launches Audit| Sentinel[Autonomous Code Sentinel]
    Sentinel -->|Read & Glob Tool Operations| Repo[Target Codebase Repository]
    Sentinel -->|Prompts + Trajectory via HTTPS SSE| ClaudeAPI[Claude Model Engine: Haiku 4.5]
    Sentinel -->|Streams Live Tokens & Findings| Terminal[Developer Console]
```

### 1.2 Level 2: Container & Process Model

```mermaid
graph TD
    subgraph Host Process [Python Runtime]
        App[sentinel.py]
        Governor[Dynamic Budget & Turn Governor]
        StreamParser[StreamEvent & ToolUseBlock Parser]
        Telemetry[Telemetry Dashboard Formatter]
    end

    subgraph Agent Subprocess [claude.exe]
        SDK_Engine[Claude Agent SDK Engine]
        Tools[Read & Glob Tool Runners]
    end

    subgraph Anthropic Gateway [Remote Cloud]
        LLM[claude-haiku-4-5-20251001]
    end

    App -->|Calculates Scope & Options| Governor
    Governor -->|Spawns query| SDK_Engine
    SDK_Engine -->|Tool Execution| Tools
    SDK_Engine -->|Token Streaming| LLM
    SDK_Engine -->|NDJSON Events| StreamParser
    StreamParser --> Telemetry
    Telemetry --> Terminal[Console Screen]
```

---

## 2. Sequence Diagram (Multi-Turn Trajectory)

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant App as sentinel.py
    participant SDK as claude.exe Subprocess
    participant LLM as Claude Haiku 4.5
    participant FS as Local Filesystem

    Dev->>App: python sentinel.py
    App->>App: Pre-Flight: Calculate Dynamic Tier (Turns & Budget)
    App->>SDK: query(prompt, options)
    SDK->>LLM: Turn 1: Discover files
    LLM-->>SDK: ToolUseBlock: Glob("*.py")
    SDK->>FS: Execute Glob
    FS-->>SDK: ['testing.py', 'sentinel.py']
    SDK->>LLM: Turn 2: Inspect candidate code
    LLM-->>SDK: ToolUseBlock: Read("testing.py")
    SDK->>FS: Read("testing.py")
    FS-->>SDK: Code Contents
    SDK->>LLM: Turn 3: Semantic bug analysis & synthesis
    LLM-->>SDK: StreamEvent chunks (Live text output)
    SDK-->>App: StreamEvent deltas
    App-->>Dev: Live streamed tokens
    LLM-->>SDK: ResultMessage(subtype="success", usage={...})
    SDK->>App: ResultMessage
    App->>Dev: Render Structured Telemetry Dashboard
```

---

## 3. Architecture Decision Records (ADRs)

### ADR-001: Dynamic Sizing over Static Constraints
- **Context:** Static turn and budget limits fail in production; 4 turns and $0.03 cannot audit multi-file codebases, while unlimited execution creates severe financial risk.
- **Decision:** Implement pre-flight dynamic budgeting based on candidate file counts (Tiers: 6/15/25 turns, $0.10/$0.40/$1.50 budgets).
- **Status:** Accepted.

### ADR-002: In-Process Read/Glob Tools over Network RPC
- **Context:** Tool calling latency must be minimized for developer pre-commit hooks ($< 20$ seconds total SLA).
- **Decision:** Use native built-in `Read` and `Glob` tools executed directly in-process by the SDK runner rather than spawning external stdio MCP processes.
- **Status:** Accepted.

### ADR-003: Model Engine Tier (Haiku 4.5)
- **Context:** Fast turnaround and high cost-efficiency are mandatory for pre-commit hooks.
- **Decision:** Use `claude-haiku-4-5-20251001` as the default engine.
- **Status:** Accepted.
