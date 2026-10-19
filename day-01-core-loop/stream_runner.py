import os, sys, asyncio
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent, ResultMessage

async def run_streaming_agent(prompt: str):
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL"),
        include_partial_messages = True,
        max_turns = 1
    )

    print("\n=== Starting streaming agent ===\n")
    print("Prompt:\n", prompt, "\n")
    print("Streaming response:\n")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", "")

                if delta.get("type") == "text_delta":
                    content = delta.get("text", "")
                    if content:
                        print(content, end="", flush=True)
                elif delta.get("type") == "thinking_delta":
                    thinking = delta.get("thinking", "")
                    if thinking:
                        print(f"\n[Thinking]: {thinking}\n", flush=True)
        elif isinstance(message, ResultMessage):
            print("\n\n=== Final response ===\n")
            print(message.result)


if __name__ == "__main__":
    prompt_text = "In 3 bullet points, explain why real-time streaming is critical for agentic user experience."
    asyncio.run(run_streaming_agent(prompt_text))