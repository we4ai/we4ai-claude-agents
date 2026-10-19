"""
Project 02: DocSync Auditor (Code & Documentation Parity Engine)
Features:
- Dynamic Tiered Budgeting based on doc + code density
- Real-Time Token Streaming (AC-01)
- Tool Call & Argument Introspection (AC-02)
- Safety Ceiling Interception (AC-03 & AC-04)
- Structured Parity Reporting & Telemetry (AC-05)
"""

import os
import sys
import glob
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment
env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

import os
import sys
import glob
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

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

# Common directories to prune from documentation & code scanning
IGNORED_DIRS: set[str] = {
    ".venv", "venv", "env", ".env",
    "__pycache__", ".git", ".pytest_cache",
    "node_modules", "dist", "build", "site-packages",
    ".idea", ".vscode"
}


@dataclass
class DocSyncTier:
    """Type-safe container for DocSync dynamic sizing."""
    max_turns: int
    max_budget_usd: float
    md_files: list[str]
    py_files: list[str]
    tier_name: str


def get_clean_files(target_dir: str, extension: str) -> list[str]:
    """Prunes third-party and cache files from discovery."""
    clean: list[str] = []
    base_path = Path(target_dir).resolve()
    for p in base_path.rglob(f"*.{extension}"):
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        try:
            clean.append(str(p.relative_to(base_path)))
        except ValueError:
            clean.append(str(p))
    return clean

def calculate_docsync_budget(target_dir: str) -> DocSyncTier:
    """Pre-flight dynamic budget calculator with strict directory pruning."""
    md_files = get_clean_files(target_dir, "md")
    py_files = get_clean_files(target_dir, "py")
    total_files = len(md_files) + len(py_files)

    if total_files <= 5:
        return DocSyncTier(
            max_turns=8, max_budget_usd=0.15,
            md_files=md_files, py_files=py_files,
            tier_name="TIER 1 (Focused Package / Small Repo)"
        )
    elif total_files <= 20:
        return DocSyncTier(
            max_turns=18, max_budget_usd=0.50,
            md_files=md_files, py_files=py_files,
            tier_name="TIER 2 (Standard Repository)"
        )
    else:
        return DocSyncTier(
            max_turns=30, max_budget_usd=2.00,
            md_files=md_files, py_files=py_files,
            tier_name="TIER 3 (Monorepo / Multi-Package)"
        )


def format_tool_call(tool_name: str, tool_input: dict) -> str:
    formatted_args = json.dumps(tool_input, indent=2)
    indented = "\n".join(f"     {line}" for line in formatted_args.splitlines())
    return f"\n🔍  [DOCSYNC ACTION]: \033[1;36m{tool_name}\033[0m\n{indented}\n"


def print_docsync_dashboard(msg: ResultMessage, tier: DocSyncTier):
    duration_sec = (msg.duration_ms or 0) / 1000
    cost = msg.total_cost_usd or 0.0
    usage = getattr(msg, "usage", {}) or {}

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    print("\n" + "╔" + "═" * 64 + "╗")
    print("║" + "           📚 DOCSYNC PARITY AUDIT TELEMETRY             ".center(64) + "║")
    print("╠" + "═" * 64 + "╣")
    print(f"║  Execution Status     : {msg.subtype:<36} ║")
    print(f"║  Dynamic Tier Applied : {tier.tier_name:<36} ║")
    print(f"║  Turns Consumed       : {msg.num_turns:<36} ║")
    print(f"║  Elapsed Time         : {duration_sec:.2f}s".ljust(65) + "║")
    print("╟" + "─" * 64 + "╢")
    print("║  TOKEN CONSUMPTION:                                            ║")
    print(f"║    • Prompt Input Tokens    : {input_tokens:<30} ║")
    print(f"║    • Output Generated Tokens: {output_tokens:<30} ║")
    print("╟" + "─" * 64 + "╢")
    print(f"║  💰 Total Audit Cost  : ${cost:.6f} / (Cap: ${tier.max_budget_usd:.2f})".ljust(65) + "║")
    print("╚" + "═" * 64 + "╝\n")


async def run_docsync(target_dir: str = "."):
    tier = calculate_docsync_budget(target_dir)

    print("=" * 66)
    print("📚  DOCSYNC AUDITOR (Code-to-Documentation Parity Engine)")
    print(f"🎯 Target Directory : {os.path.abspath(target_dir)}")
    print(f"📄 Files Discovered : {len(tier.md_files)} markdown docs, {len(tier.py_files)} python files")
    print(f"⚡ Dynamic Sizing   : {tier.tier_name}")
    print(f"🛑 Guardrails       : max_turns={tier.max_turns} | max_budget=${tier.max_budget_usd:.2f}")
    print("=" * 66 + "\n")

    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        include_partial_messages=True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=tier.max_turns,
        max_budget_usd=tier.max_budget_usd
    )

    prompt = f"""
    You are DocSync Auditor, an automated documentation and code parity inspector.

    Target Directory: '{target_dir}'
    
    Instructions:
    1. Call Glob to list .md and .py files.
    2. Inspect testing.py using Read tool to extract actual implemented functions.
    3. Generate a Markdown Documentation Parity Scorecard:
       - Implemented Functions found in code
       - Status (Verified Parity / Stale Signature / Undocumented)
       - Drift Summary and Actionable Recommendations for docs
    """

    print("🤖 DocSync Analysis & Live Stream:\n")

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        print(delta.get("text", ""), end="", flush=True)

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(format_tool_call(block.name, block.input))

            elif isinstance(message, ResultMessage):
                print_docsync_dashboard(message, tier)

    except ResultError as e:
        print("\n\n" + "🛑" * 30)
        print(f"Safety Ceiling Intercepted: {e.subtype}")
        print(f"Details: {e.errors}")
        print("🛑" * 30)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(run_docsync(target))
