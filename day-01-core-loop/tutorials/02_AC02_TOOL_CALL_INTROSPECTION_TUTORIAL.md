# 🛠️ AC-02 Master Tutorial: Tool Call & Argument Introspection in Claude Agent SDK

> **Module:** Day 01 - Core Agent Execution Loop  
> **Topic:** Acceptance Criteria 02 (AC-02: Tool Calls & Argument Introspection)  
> **Language:** Hinglish (Desi Tech Breakdown) + Production Python Patterns  
> **Format:** Audio-Friendly / Read-Aloud Tutorial  

---

## 🎧 Part 1: The "Why" - Tool Call Introspection Kyun Zaroori Hai?

AC-01 mein humne dekha ki model jo **bolta hai** (text), usko live stream kaise karte hain.  
Lekin Claude sirf ek chatbot nahi hai; Claude ek **Agent** hai!  
Agent ka matlab hota hai: **Thinking + Action (Tool Execution)**.

### Imagine Karo Ek Dangerous Scenario:
Tumne agent ko bola: *"Clean up old test files in this project."*  
Agent backend mein silently kaam kar raha hai:
- Pehle usne `Glob` tool chalaya.
- Fir usne `Bash` tool chalaya: `rm -rf /` ya galat folder delete kar diya!

Agar tumhara system sirf **final output text** print karta hai, toh jab tak agent bolna band karega, tab tak tumhara system crash ho chuka hoga!

**Real-world Analogy:**  
Socho tumne ek junior developer ko bola *"Production database optimize kar do"*.  
Wo chupchap apne laptop pe kuch type kare aur 10 minute baad bole *"Done sir!"*  
Bina yeh dekhe ki usne SQL query kya chalayi thi, kya tum chain ki neend so sakte ho? Bilkul nahi!

**AC-02 ka Goal:**  
Jab bhi Claude koi tool chalane ka faisla kare, hamare terminal par **transparently and clearly** dikhna chahiye:
1. Tool ka naam kya hai (`tool_name`, e.g. `Read`, `Edit`, `Glob`, `Bash`).
2. Model ne us tool ko kya **parameters / inputs** pass kiye (`input_arguments`).
3. Tool execute hone ke baad kya result aaya (`ToolResultBlock`).

---

## ⚙️ Part 2: SDK ke Andar Tool Call Kaise Aata Hai?

Jab Claude kisi task ko poora karne ke liye tool use karta hai, toh message lifecycle mein ek specific block generate hota hai: **`ToolUseBlock`**.

```
[ Claude Model decides to act ]
               │
               ▼
       AssistantMessage
               │
        ┌──────┴────────────────────────┐
        ▼                               ▼
   [ TextBlock ]                [ ToolUseBlock ]
("I will read the file...")    id: "toolu_01Abc"
                               name: "Read"
                               input: {"file_path": "testing.py"}
```

### ToolUseBlock ki Anatomy (SDK Types):
```python
@dataclass
class ToolUseBlock:
    id: str                # Unique invocation ID (e.g., 'toolu_011Cg...')
    name: str              # Tool ka naam: 'Read', 'Edit', 'Bash', etc.
    input: dict[str, Any]  # Tool ke arguments (JSON dict)
```

Aur jab tool execute ho jata hai, tab agle message mein uska result aata hai:
```python
@dataclass
class ToolResultBlock:
    tool_use_id: str                          # Kiske response mein ye result hai
    content: str | list[dict[str, Any]] | None # Output text ya data
    is_error: bool | None                     # Kya tool fail hua?
```

---

## 🧩 Part 3: Tool Use vs StreamEvent: Kahan Dhundhein?

Tool calls do alag tareeqon se capture kiye ja sakte hain:

### Tareeqa A: `AssistantMessage` ke andar (Sabse Clean & Stable)
Jab turn poora hota hai, Claude ka `AssistantMessage` aata hai.  
Iske `.content` list ke andar alag-alag blocks hote hain:
- Kuch blocks `TextBlock` hote hain (`block.text`).
- Kuch blocks `ToolUseBlock` hote hain (`block.name`, `block.input`).

```python
if isinstance(message, AssistantMessage):
    for block in message.content:
        # Check if this block is a tool call
        if isinstance(block, ToolUseBlock):
            print(f"🛠️ [TOOL INVOKED]: {block.name}")
            print(f"   Inputs: {json.dumps(block.input, indent=2)}")
```

### Tareeqa B: Streaming Mode mein (`StreamEvent`)
Streaming mode mein jab tool call start hota hai:
- `event["type"] == "content_block_start"`
- `event["content_block"]["type"] == "tool_use"`
- `event["content_block"]["name"] == "Read"`
- Iske baad `content_block_delta` aate hain jisme `input_json_delta` stream hota hai!

> **Best Practice Tip for AC-02:**  
> Live streaming mein raw JSON ke fragmented chunks read karne ke bajaye, `AssistantMessage` ke andar aane wale parsed `ToolUseBlock` ko print karna 100% clean aur formatted hota hai, kyunki SDK arguments ko already ek valid Python dictionary (`block.input`) mein parse kar chuka hota hai!

---

## 🛠️ Part 4: Complete Implementation Pattern (AC-02)

Chalo ek reusable formatter banate hain jo:
1. Normal text ko live stream kare (AC-01).
2. Tool call aate hi distinct highlight karke tool ka naam aur arguments print kare (AC-02).
3. Tool execution fail hui ya pass, wo bhi bataye.

```python
import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Windows console safety
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import (
    StreamEvent,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)


def format_tool_call(tool_name: str, tool_input: dict) -> str:
    """Pretty prints tool invocations with JSON syntax."""
    formatted_args = json.dumps(tool_input, indent=4)
    # Indent every line for neat console hierarchy
    indented = "\n".join(f"     {line}" for line in formatted_args.splitlines())
    return f"\n🛠️  [TOOL CALLED]: \033[1;33m{tool_name}\033[0m\n{indented}\n"


async def run_tool_introspection_agent():
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        allowed_tools=["Read", "Glob"],
        permission_mode="default",
        max_turns=3,
    )

    prompt = "Find all python files in the current folder using Glob, and inspect testing.py using Read."

    print(f"👤 User: {prompt}\n")
    print("🤖 Agent Output:")

    async for message in query(prompt=prompt, options=options):
        # 1. AC-01: Live Text Token Streaming
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    print(delta.get("text", ""), end="", flush=True)

        # 2. AC-02: Tool Call & Argument Introspection
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(format_tool_call(block.name, block.input))

        # 3. Final Summary
        elif isinstance(message, ResultMessage):
            print("\n" + "=" * 50)
            print(f"🏁 Finished | Turns: {message.num_turns} | Cost: ${message.total_cost_usd or 0:.4f}")
            print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_tool_introspection_agent())
```

---

## 🎯 Part 5: Acceptance Criteria Checklist for AC-02

- [x] Catch `isinstance(block, ToolUseBlock)` inside `AssistantMessage.content`.
- [x] Print `block.name` clearly with visual distinction (emoji / color).
- [x] Serialize and pretty-print `block.input` dictionary as JSON.
- [x] Verify tool invocation transparency on built-in tools (`Read`, `Edit`, `Glob`).
- [x] Zero loss of real-time streaming capability (AC-01 + AC-02 work harmoniously together).

---

## 💡 Quick Recall Quiz:

1. **Question:** `ToolUseBlock` ke paas do sabse important attributes kaun se hote hain?  
   **Answer:** `name` (tool ka naam) aur `input` (dictionary of arguments).
2. **Question:** Tool ka unique ID kyu hota hai (`block.id`)?  
   **Answer:** Taaki jab tool run ho kar result aaye, toh system match kar sake ki ye result kis tool invocation ka tha (`tool_use_id`).
3. **Question:** Agar agent ko bina tool inspection ke production mein chalayein toh sabse bada risk kya hai?  
   **Answer:** Unsafe mutations ya destructive actions (e.g. wrong file delete/edit, unsafe bash commands) blind spot ban jaate hain.
