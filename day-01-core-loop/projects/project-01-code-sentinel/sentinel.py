"""
Autonomous Code Sentinel (Production Implementation)
Features:
- Dynamic Tiered Budgeting (Scales turns & budget based on codebase size)
- Real-Time Token Streaming (AC-01)
- Tool Call & Argument Introspection (AC-02)
- Safety Ceiling Interception (AC-03 & AC-04)
- Structured Telemetry & Cost Accounting (AC-05)
"""

import os
import sys
import glob
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure Windows UTF-8 Safe Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment
env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import (
    StreamEvent, AssistantMessage, ToolUseBlock, ResultMessage
)


import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Ensure Windows UTF-8 Safe Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment
env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import (
    StreamEvent, AssistantMessage, ToolUseBlock, ResultMessage
)

# ============================================================================
# 1. ENTERPRISE FILTERING CONSTANTS
# ============================================================================
# Directories that must NEVER be analyzed (dependencies, virtualenvs, caches)
IGNORED_DIRS: set[str] = {
    ".venv", "venv", "env", ".env",
    "__pycache__", ".git", ".pytest_cache",
    "node_modules", "dist", "build", "site-packages",
    ".idea", ".vscode", ".tox"
}

# Self-referential scripts to exclude from security audit
IGNORED_FILES: set[str] = {
    "sentinel.py", "agent.py", "conftest.py"
}


# ============================================================================
# 2. TYPE-SAFE DATA MODELS
# ============================================================================
@dataclass
class BudgetTier:
    """Type-safe container for dynamic sizing and execution guardrails."""
    max_turns: int
    max_budget_usd: float
    candidate_files: list[str]
    tier_name: str
    detection_mode: str  # "GIT_STAGED", "GIT_MODIFIED", or "FILTERED_WORKSPACE"


# ============================================================================
# 3. GIT DIFF AWARENESS & DISCOVERY ENGINE
# ============================================================================
def get_git_changed_files(target_dir: str) -> tuple[list[str], str]:
    """
    Inspects Git status to focus audit strictly on the blast-radius of changes:
    1. First checks for staged files (pre-commit: git diff --cached).
    2. Falls back to uncommitted modified files (working tree: git diff HEAD).
    """
    try:
        # Check staged files (pre-commit hook standard)
        res_staged = subprocess.run(
            ["git", "-C", target_dir, "diff", "--name-only", "--cached"],
            capture_output=True, text=True, check=False
        )
        staged_files = [
            f for f in res_staged.stdout.splitlines() 
            if f.endswith(".py") and Path(f).name not in IGNORED_FILES
        ]
        if staged_files:
            return staged_files, "GIT_STAGED_DIFF (Pre-Commit Staged Files)"

        # Fall back to working-tree modifications against HEAD
        res_modified = subprocess.run(
            ["git", "-C", target_dir, "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, check=False
        )
        modified_files = [
            f for f in res_modified.stdout.splitlines()
            if f.endswith(".py") and Path(f).name not in IGNORED_FILES
        ]
        if modified_files:
            return modified_files, "GIT_MODIFIED_DIFF (Working Tree Changes)"

    except Exception:
        # Not a git repo, git binary missing, or git error -> fallback to workspace scan
        pass

    return [], "NONE"


def get_filtered_workspace_files(target_dir: str) -> list[str]:
    """
    Recursively scans target directory while strictly pruning ignored directories
    (virtualenvs, build artifacts, node_modules) to prevent token pollution.
    """
    clean_files: list[str] = []
    base_path = Path(target_dir).resolve()

    for path in base_path.rglob("*.py"):
        # Prune if any directory component matches IGNORED_DIRS
        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        # Prune runner scripts
        if path.name in IGNORED_FILES:
            continue

        # Keep relative path for clean agent prompts
        try:
            rel_path = path.relative_to(base_path)
            clean_files.append(str(rel_path))
        except ValueError:
            clean_files.append(str(path))

    return clean_files


def calculate_dynamic_budget(target_dir: str) -> BudgetTier:
    """
    Dynamic Sizing Engine:
    Prioritizes Git diff blast-radius. If no git changes detected,
    performs a clean, filtered workspace scan to scale turns & budget.
    """
    # 1. Try Git Diff Awareness first (Shift-Left Pre-Commit Best Practice)
    git_files, git_mode = get_git_changed_files(target_dir)

    if git_files:
        candidate_files = git_files
        detection_mode = git_mode
    else:
        # 2. Fall back to clean filtered directory traversal
        candidate_files = get_filtered_workspace_files(target_dir)
        detection_mode = "FILTERED_WORKSPACE_SCAN (Strict Pruned)"

    file_count = len(candidate_files)

    # 3. Dynamic Tier Allocation
    if file_count <= 2:
        # Tier 1: Micro / Hotfix Diff (1-2 files)
        return BudgetTier(
            max_turns=6,
            max_budget_usd=0.10,
            candidate_files=candidate_files,
            tier_name="TIER 1 (Micro / Hotfix Diff)",
            detection_mode=detection_mode
        )
    elif file_count <= 10:
        # Tier 2: Standard Feature / Module Audit (3-10 files)
        return BudgetTier(
            max_turns=15,
            max_budget_usd=0.40,
            candidate_files=candidate_files,
            tier_name="TIER 2 (Standard Module / PR)",
            detection_mode=detection_mode
        )
    else:
        # Tier 3: Subsystem / Architectural Review (> 10 files)
        return BudgetTier(
            max_turns=25,
            max_budget_usd=1.50,
            candidate_files=candidate_files,
            tier_name="TIER 3 (Subsystem Monorepo Audit)",
            detection_mode=detection_mode
        )


def format_tool_call(tool_name: str, tool_input: dict) -> str:
    """Pretty prints tool invocations with JSON syntax."""
    formatted_args = json.dumps(tool_input, indent=2)
    indented = "\n".join(f"     {line}" for line in formatted_args.splitlines())
    return f"\n🛠️  [SENTINEL ACTION]: \033[1;33m{tool_name}\033[0m\n{indented}\n"


def print_sentinel_dashboard(msg: ResultMessage, tier: BudgetTier):
    """Renders enterprise telemetry report."""
    duration_sec = (msg.duration_ms or 0) / 1000
    cost = msg.total_cost_usd or 0.0
    usage = getattr(msg, "usage", {}) or {}

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)

    print("\n" + "╔" + "═" * 64 + "╗")
    print("║" + "           🛡️ AUTONOMOUS CODE SENTINEL TELEMETRY         ".center(64) + "║")
    print("╠" + "═" * 64 + "╣")
    print(f"║  Execution Status     : {msg.subtype:<36} ║")
    print(f"║  Detection Mode       : {tier.detection_mode[:36]:<36} ║")
    print(f"║  Dynamic Tier Applied : {tier.tier_name:<36} ║")
    print(f"║  Turns Consumed       : {msg.num_turns:<36} ║")
    print(f"║  Elapsed Time         : {duration_sec:.2f}s".ljust(65) + "║")
    print("╟" + "─" * 64 + "╢")
    print("║  TOKEN ACCOUNTING:                                             ║")
    print(f"║    • Prompt Input Tokens    : {input_tokens:<30} ║")
    print(f"║    • Output Generated Tokens: {output_tokens:<30} ║")
    print(f"║    • Prompt Cache Read      : {cache_read:<30} ║")
    print("╟" + "─" * 64 + "╢")
    print(f"║  💰 Total Audit Cost  : ${cost:.6f} / (Cap: ${tier.max_budget_usd:.2f})".ljust(65) + "║")
    print("╚" + "═" * 64 + "╝\n")


async def run_sentinel(target_dir: str = "."):
    # 1. Pre-flight Dynamic Sizing with Git-Diff & Ignored-Dir Filtering
    tier = calculate_dynamic_budget(target_dir)

    print("=" * 66)
    print("🛡️  AUTONOMOUS CODE SENTINEL (Shift-Left Security Gate)")
    print(f"🎯 Target Directory : {os.path.abspath(target_dir)}")
    print(f"🔍 Discovery Mode   : {tier.detection_mode}")
    print(f"📁 Candidate Files  : {len(tier.candidate_files)} files: {tier.candidate_files[:5]}")
    print(f"⚡ Dynamic Sizing   : {tier.tier_name}")
    print(f"🛑 Guardrails       : max_turns={tier.max_turns} | max_budget=${tier.max_budget_usd:.2f}")
    print("=" * 66 + "\n")

    if not tier.candidate_files:
        print("ℹ️ No modified or eligible Python files found to audit. Exiting cleanly.")
        return

    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        include_partial_messages=True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=tier.max_turns,
        max_budget_usd=tier.max_budget_usd
    )

    files_str = "\n".join(f"- {f}" for f in tier.candidate_files)
    prompt = f"""
    You are Autonomous Code Sentinel, a staff security and code reliability auditor.

    Candidate files to audit:
{files_str}

    Instructions:
    1. Inspect the candidate files using the Read tool.
    2. Analyze implementations for crash bugs (ZeroDivisionError, NoneType indexing, unhandled exceptions, type errors).
    3. Output a structured Markdown Findings Table:
       - Severity (Critical / Warning / Info)
       - File & Function Name
       - Issue Description
       - Recommended Surgical Fix
    """

    print("🤖 Sentinel Reasoning & Stream:\n")

    try:
        async for message in query(prompt=prompt, options=options):
            # AC-01: Live Text Stream
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        print(delta.get("text", ""), end="", flush=True)

            # AC-02: Tool Call Introspection
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(format_tool_call(block.name, block.input))

            # AC-05: Telemetry Dashboard
            elif isinstance(message, ResultMessage):
                print_sentinel_dashboard(message, tier)

    except ResultError as e:
        print("\n\n" + "🛑" * 30)
        print(f"Safety Ceiling Intercepted: {e.subtype}")
        print(f"Details: {e.errors}")
        print("🛑" * 30)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(run_sentinel(target))
