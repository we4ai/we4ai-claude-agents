import os, sys, json, asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import AssistantMessage, ToolUseBlock, ResultMessage, TextBlock


async def inspect_real_turns():
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=3,
        include_partial_messages=False
    )

    prompt = "Find all python files in this folder using Glob, then inspect testing.py using Read. Then find all md files."

    print("=" * 65)
    print("🔍 ACCURATE TURN-BY-TURN INSPECTOR (Deduplicated)")
    print("=" * 65 + "\n")

    seen_turn_ids = set()
    actual_turn_count = 0

    try:
        async for message in query(prompt=prompt, options=options):
            
            if isinstance(message, AssistantMessage):
                msg_id = getattr(message, "message_id", None)
                
                # Agar ye naya message_id hai, tabhi actual NAYA TURN shuru hua!
                if msg_id and msg_id not in seen_turn_ids:
                    seen_turn_ids.add(msg_id)
                    actual_turn_count += 1
                    
                    print(f"\n╔{'═' * 60}╗")
                    print(f"║ 🔄 ACTUAL TURN #{actual_turn_count}".ljust(61) + "║")
                    print(f"║ API Message ID : {msg_id}".ljust(61) + "║")
                    print(f"║ Stop Reason    : {getattr(message, 'stop_reason', 'N/A')}".ljust(61) + "║")
                    print(f"╠{'═' * 60}╣")

                    for block in message.content:
                        if isinstance(block, TextBlock):
                            clean_text = block.text.strip()
                            if clean_text:
                                print(f"║ 💬 Text: {clean_text[:80]}...")
                        elif isinstance(block, ToolUseBlock):
                            print(f"║ 🛠️  Tool: {block.name} with input {block.input}")

                    print(f"╚{'═' * 60}╝")

            elif isinstance(message, ResultMessage):
                print("\n" + "=" * 65)
                print(f"🏁 Final Result: {message.subtype}")
                print(f"🎯 SDK Verified Total Turns : {message.num_turns}")
                print(f"🔢 Our Deduplicated Turns    : {actual_turn_count}")
                print("=" * 65)

    except ResultError as e:
        print("\n" + "🛑" * 30)
        print(f"Safety Ceiling Hit: {e.subtype}")
        print(f"Actual Turns Taken Before Halt: {actual_turn_count}")
        print("🛑" * 30)


if __name__ == "__main__":
    asyncio.run(inspect_real_turns())