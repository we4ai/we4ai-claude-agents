import os, sys, json, asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
# 👈 ResultError ko import karo!
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import StreamEvent, ResultMessage, AssistantMessage, ToolUseBlock


async def run_safe_turns_agent():
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=3  # Hard ceiling
    )
    
    prompt = "Find all python files in the folder using Glob and inspect testing.py using Read. Then find the md files as well."

    print("🚀 Starting agent with max_turns=3...\n")

    try:
        async for message in query(prompt=prompt, options=options):
            # 1. Real-time text stream
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        print(delta.get("text", ""), end="", flush=True)

            # 2. Tool invocations
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"\n🛠️  Tool Use: {block.name} -> {block.input}")

            # 3. Normal Result (agar 3 turns ke andar complete ho gaya)
            elif isinstance(message, ResultMessage):
                print(f"\n\n✅ Finished normally in {message.num_turns} turns!")

    # 4. 🛑 CATCH THE BOUNDARY CEILING ERROR GRACEFULLY!
    except ResultError as e:
        if e.subtype == "error_max_turns":
            print("\n\n" + "=" * 50)
            print("🛡️  SAFETY CEILING TRIGGERED: 'error_max_turns'")
            print("   The agent was stopped safely because it hit the 3-turn limit.")
            print(f"   Errors reported: {e.errors}")
            print("=" * 50)
        else:
            print(f"\n\n⚠️ Other ResultError occurred: {e.subtype} - {e}")


if __name__ == "__main__":
    asyncio.run(run_safe_turns_agent())