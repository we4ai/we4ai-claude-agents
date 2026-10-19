import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Search for .env in current directory and parent directories
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Review testing.py for bugs that would cause crashes. Fix any sisues you find.",
        options=ClaudeAgentOptions(
            model="claude-sonnet-4-5-20250929",
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits"        
        )
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")
        elif isinstance(message, ResultMessage):
            print("Result subtype:", message.subtype)
            print("Result is_error:", message.is_error)
            print("Result output:", message.result)
            if message.errors:
                print("Result errors:", message.errors)

asyncio.run(main())
