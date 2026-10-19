import os
import sys
import asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError, CLIConnectionError, CLINotFoundError
from claude_agent_sdk.types import StreamEvent, ResultMessage


async def run_budget_bounded_agent():
    # AC-04: Micro budget jo turant exceed ho sake testing ke liye
    tight_budget = 0.0001  # $0.0001 USD
    
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        max_budget_usd=tight_budget,  # 👈 Financial Safeguard
    )

    prompt = "Write an essay explaining the history of computing from Charles Babbage to quantum computers."

    print(f"💰 Configured max_budget_usd : ${tight_budget:.6f}")
    print(f"👤 User: {prompt}\n")
    print("🤖 Agent Output:\n")

    try:
        async for message in query(prompt=prompt, options=options):
            # Stream text live
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        print(delta.get("text", ""), end="", flush=True)

            # Check ResultMessage for normal completion
            elif isinstance(message, ResultMessage):
                print("\n" + "=" * 50)
                print("🛑 Run Completed Normally!")
                print(f"  Result Subtype : {message.subtype}")
                print(f"  Total Cost     : ${message.total_cost_usd or 0:.6f}")
                print("=" * 50)

    except ResultError as e:
        # SDK throws ResultError when budget or turn limit causes CLI non-zero exit
        print("\n\n" + "=" * 50)
        print("🛑 ResultError Intercepted Gracefully!")
        print(f"  Subtype   : {e.subtype}")
        print(f"  Errors    : {e.errors}")
        print("=" * 50)

        if e.subtype == "error_max_budget_usd":
            print("✅ AC-04 PASSED: Hard financial cap triggered successfully!")
            print("   Agent was cleanly stopped by SDK before burning money.")
        else:
            print(f"⚠️ Terminated with other error subtype: {e.subtype}")

    except CLINotFoundError:
        print("\n❌ Error: Claude Code CLI binary not found.")
    except CLIConnectionError as e:
        print(f"\n❌ Connection Error with Claude CLI: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error occurred: {type(e).__name__} - {e}")


if __name__ == "__main__":
    asyncio.run(run_budget_bounded_agent())
