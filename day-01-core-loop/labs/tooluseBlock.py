import os, sys, json, asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import (
    StreamEvent, ResultMessage,
    AssistantMessage, UserMessage, SystemMessage,
    ToolUseBlock, ToolResultBlock
)

def format_tool_call(tool_name, tool_input):
    formatted_args = json.dumps(tool_input, indent=4)
    indented = "\n".join(f"    {line}"  for line in formatted_args.splitlines())
    return f"Tool Call:\n  Tool Name: {tool_name}\n  Tool Input:\n{indented}\n"

async def run_tool_introspection_agent():
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL"),
        include_partial_messages = True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns = 10
    )
    prompt = "Find all python files in the folder using Glob and inspect testing.py using Read"
    print("User Prompt:\n", prompt, "\n")
    print("Agent Output:\n")
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    print(delta.get("text", ""), end="", flush=True)

        elif isinstance(message, AssistantMessage):
            print("\n\nAssistant Message:\n", message.content, "\n")
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print()
                    print(format_tool_call(block.name, block.input))
        elif isinstance(message, ResultMessage):
            print("\n\nFinal Result:\n")
            print(message.result)


asyncio.run(run_tool_introspection_agent()) 