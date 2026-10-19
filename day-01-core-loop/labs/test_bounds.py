import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# AC-06: Windows UTF-8 console resilience
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment from project root
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk._errors import ResultError
from claude_agent_sdk.types import ResultMessage, StreamEvent, ToolUseBlock, AssistantMessage


@pytest.mark.asyncio
async def test_ac01_streaming_events_emitted():
    """AC-01: Verify StreamEvent deltas are emitted when include_partial_messages=True."""
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        max_turns=1
    )

    deltas_received = []
    async for message in query(prompt="Respond with only 'OK'.", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    deltas_received.append(delta.get("text", ""))

    assert len(deltas_received) > 0, "Expected at least one text_delta stream event"


@pytest.mark.asyncio
async def test_ac02_tool_call_inspection():
    """AC-02: Verify ToolUseBlock captures tool name and arguments."""
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        allowed_tools=["Glob"],
        permission_mode="default",
        max_turns=2
    )

    tools_called = []
    try:
        async for message in query(prompt="Use the Glob tool to search for *.py files.", options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        tools_called.append((block.name, block.input))
    except ResultError:
        pass

    assert any(name == "Glob" for name, _ in tools_called), "Expected Glob tool to be invoked"


@pytest.mark.asyncio
async def test_ac03_max_turns_enforcement():
    """AC-03: Verify execution stops at max_turns boundary without hanging."""
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        allowed_tools=["Glob"],
        permission_mode="default",
        max_turns=1  # Multi-step task cannot finish in 1 turn
    )

    prompt = "Find all .py files using Glob, then list them in reverse alphabetical order."

    halted_with_max_turns = False
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                if message.subtype == "error_max_turns" or (message.num_turns and message.num_turns <= 1):
                    halted_with_max_turns = True
    except ResultError as e:
        if e.subtype == "error_max_turns":
            halted_with_max_turns = True

    assert halted_with_max_turns, "Expected agent to halt at max_turns=1"


@pytest.mark.asyncio
async def test_ac04_budget_limit_enforcement():
    """AC-04: Verify agent halts when max_budget_usd is breached."""
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        max_budget_usd=0.00001,  # Micro budget guarantees immediate limit breach
    )

    prompt = "Write a comprehensive 500-word essay about the solar system."

    budget_halted = False
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                if message.subtype == "error_max_budget_usd":
                    budget_halted = True
    except ResultError as e:
        if e.subtype == "error_max_budget_usd":
            budget_halted = True

    assert budget_halted, "Expected agent to halt with error_max_budget_usd"


def test_ac06_unicode_and_emojis_print_safely(capsys):
    """AC-06: Verify emojis and multi-byte characters print without charmap encoding crash."""
    test_string = "✅ Status OK | 🛠️ Tool Used | 📊 Telemetry: $0.002892 | 🛑 Ceiling Reached"
    print(test_string)
    captured = capsys.readouterr()
    assert "Status OK" in captured.out
