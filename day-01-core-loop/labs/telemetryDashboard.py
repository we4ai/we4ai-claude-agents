import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure Windows terminal handles UTF-8 box-drawing and emoji characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import ResultMessage, StreamEvent, AssistantMessage, ToolUseBlock


def render_telemetry_dashboard(msg: ResultMessage):
    """
    AC-05: Renders an enterprise-grade observability & cost accounting report.
    """
    duration_total_sec = (msg.duration_ms or 0) / 1000
    duration_api_sec = (getattr(msg, "duration_api_ms", 0) or 0) / 1000
    local_processing_sec = max(0.0, duration_total_sec - duration_api_sec)
    
    total_cost = msg.total_cost_usd or 0.0
    usage = getattr(msg, "usage", {}) or {}

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    cache_creation = usage.get("cache_creation_input_tokens", 0)
    total_tokens = input_tokens + output_tokens + cache_read + cache_creation

    # Status indicator icon
    status_icon = "✅" if msg.subtype == "success" else "🛑"

    print("\n" + "╔" + "═" * 62 + "╗")
    print("║" + "             📊 AGENT RUN TELEMETRY REPORT            ".center(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print(f"║  Execution Status   : {status_icon} {msg.subtype:<33} ║")
    print(f"║  Conversation Turns : {msg.num_turns:<38} ║")
    print(f"║  Total Elapsed Time : {duration_total_sec:.2f}s".ljust(63) + "║")
    print(f"║    • API Wait Time  : {duration_api_sec:.2f}s".ljust(63) + "║")
    print(f"║    • Local Compute  : {local_processing_sec:.2f}s".ljust(63) + "║")
    print("╟" + "─" * 62 + "╢")
    print("║  TOKEN CONSUMPTION METRICS:                                  ║")
    print(f"║    • Prompt (Input) Tokens    : {input_tokens:<28} ║")
    print(f"║    • Generated (Output) Tokens: {output_tokens:<28} ║")
    print(f"║    • Cache Read Tokens        : {cache_read:<28} ║")
    if cache_creation > 0:
        print(f"║    • Cache Written Tokens     : {cache_creation:<28} ║")
    print(f"║    • Total Tokens Processed   : {total_tokens:<28} ║")
    print("╟" + "─" * 62 + "╢")
    print(f"║  💰 Total Financial Cost (USD): ${total_cost:.6f}".ljust(63) + "║")
    print("╚" + "═" * 62 + "╝\n")


async def run_telemetry_agent():
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=10,
        max_budget_usd=0.5
    )

    prompt = "Inspect testing.py using Read tool and explain in 2 bullet points what it does."

    print(f"👤 User: {prompt}\n")
    print("🤖 Agent Output:\n")

    try:
        async for message in query(prompt=prompt, options=options):
            # 1. AC-01: Live Text Stream
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        print(delta.get("text", ""), end="", flush=True)

            # 2. AC-02: Tool Call Introspection
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"\n🛠️  [Tool Call]: {block.name} -> {block.input}")

            # 3. AC-05: Final Telemetry Dashboard
            elif isinstance(message, ResultMessage):
                render_telemetry_dashboard(message)

    except ResultError as e:
        print(f"\n\n🛑 Boundary hit: {e.subtype} | Details: {e.errors}")


if __name__ == "__main__":
    asyncio.run(run_telemetry_agent())
