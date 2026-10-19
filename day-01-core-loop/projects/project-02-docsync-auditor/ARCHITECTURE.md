# 🏛️ System Architecture & Design
## DocSync Auditor

---

## 1. C4 Architecture Models

### 1.1 Level 1: System Context Diagram

```mermaid
graph TD
    User[Developer / Technical Writer] -->|Launches Audit| Auditor[DocSync Auditor]
    Auditor -->|Reads Documentation & Code| LocalRepo[Local Git Repository]
    Auditor -->|Semantic Evaluation via Claude Agent SDK| LLM[Claude Haiku 4.5]
    Auditor -->|Outputs Parity Scorecard| Console[Terminal / CI Report]
```

### 1.2 Level 2: Component Architecture

```mermaid
graph TD
    subgraph DocSync Runtime
        App[auditor.py]
        Sizing[Dynamic Tier Governor]
        Parser[StreamEvent & ToolUseBlock Formatter]
        Scorecard[Drift Scorecard Generator]
    end

    subgraph Agent Subprocess [Claude Agent SDK]
        CLI[claude.exe Engine]
        Tools[Read & Glob Tool Runners]
    end

    App --> Sizing
    Sizing --> CLI
    CLI --> Tools
    CLI --> Parser
    Parser --> Scorecard
    Scorecard --> Terminal[Console Screen]
```

---

## 2. Architecture Decision Records (ADRs)

### ADR-001: Read-Only Governance in Phase 1
- **Decision:** The agent performs audit and parity analysis only; it does not write or mutate markdown files autonomously without human sign-off.
- **Status:** Accepted.

### ADR-002: Dynamic Footprint Sizing
- **Decision:** Budget and turn ceilings scale dynamically with the sum of markdown and code files discovered.
- **Status:** Accepted.
