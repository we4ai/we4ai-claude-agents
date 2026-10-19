# 🎙️ AC-01 Master Tutorial: Real-Time Token Streaming in Claude Agent SDK

> **Module:** Day 01 - Core Agent Execution Loop  
> **Topic:** Acceptance Criteria 01 (AC-01: Real-Time Token Streaming)  
> **Language:** Hinglish (Desi Tech Breakdown) + Production Python Patterns  
> **Format:** Audio-Friendly / Read-Aloud Tutorial  

---

## 🎧 Part 1: The "Why" - Asli Problem Kya Thi?

Socho tum ek restaurant mein gaye aur waiter se poocha:  
*"Bhaiya, aaj special mein kya hai?"*

Waiter agle **25 second tak bilkul silent khada rahe**... aakhein band karke.  
Tum sochoge:  
- *"Yeh sun raha hai kya?"*  
- *"System freeze ho gaya?"*  
- *"Chala jaaun kya yahan se?"*  

Aur 25 second baad achanak wo bina saans liye 40 items ek second mein bol de!  

Yeh exact problem hoti hai jab hum LLM agent ko **non-streaming (batch)** mode mein run karte hain:
- Agent backend mein `claude.exe` ko call karta hai.
- Model sochna shuru karta hai.
- Terminal / UI pe **complete pin-drop silence** hota hai.
- Jab pura response taiyaar ho jata hai, tab screen pe ek saath pura text **dump** ho jata hai.

**AC-01 ka Goal:**  
Humein bilkul ChatGPT / Claude web jaisa **real-time live typing effect** chahiye. Jaise hi model ke dimaag mein ek word (token) trigger ho, agle hi millisecond wo terminal pe tapakna chahiye!

---

## ⚙️ Part 2: Under The Hood - SDK Streaming Engine

Claude Agent SDK ka architecture samajhna bohot zaroori hai.

```
[ Python Script (Hamara Code) ]
         │
         │  (Stdin / Stdout Pipes - NDJSON Lines)
         ▼
[ Bundled CLI Process (`claude.exe`) ]
         │
         │  (HTTP SSE Streaming)
         ▼
[ Claude Model (api.anthropic.com / claude.vocareum.com) ]
```

### Normal Mode vs Streaming Mode:
1. **Normal Mode (`include_partial_messages=False`, Default):**  
   CLI model se saare tokens collect karta hai. Jab turn complete hota hai, tab Python ko ek bada consolidated `AssistantMessage` bhejta hai.
2. **Streaming Mode (`include_partial_messages=True`):**  
   CLI model ka **Server-Sent Event (SSE)** stream directly pipe pe pass karta hai as individual **`StreamEvent`** objects!

---

## 🧩 Part 3: Message Lifecycle & StreamEvent Anatomy

Jab streaming on hoti hai, toh hume loop mein alag-alag type ke objects milte hain. Unka sequence aisa hota hai:

### 1. `SystemMessage`
- **Kyu aata hai?** Session initialize hua, task start hua.
- **Dhyan rakhne wali baat:** Iske paas `.event` attribute **nahi** hota. Agar bina check kare `message.event` likha toh `AttributeError` aayega!

### 2. `StreamEvent` (The Star of AC-01 ⭐)
Har token aane par ek `StreamEvent` emit hota hai. Iska structure Anthropic Messages API specification ko follow karta hai:

```python
StreamEvent(
    uuid="...",
    session_id="...",
    event={
        "type": "content_block_delta",
        "index": 0,
        "delta": {
            "type": "text_delta",
            "text": "Hello"   # 👈 Ye raha tumhara live token!
        }
    }
)
```

#### Event ke 3 stages hote hain:
- **`content_block_start`**: Claude ne naya block shuru kiya (e.g. Text shuru ho raha hai ya Tool Call).
- **`content_block_delta`**: Model continuous tokens bhej raha hai.
  - `delta["type"] == "text_delta"`: Normal user-facing output text.
  - `delta["type"] == "thinking_delta"`: Extended thinking reasoning tokens.
- **`content_block_stop`**: Current block finish ho gaya.

### 3. `AssistantMessage`
- Tokens complete hone ke baad poora aggregated message (with `TextBlock` & `ToolUseBlock`).

### 4. `ResultMessage`
- Pura execution finish! Isme metadata hota hai: `duration_ms`, `total_cost_usd`, `num_turns`, `subtype`.

---

## 🛠️ Part 4: Production Implementation for AC-01

AC-01 pass karne ke liye 3 engineering golden rules hain:

1. **`flush=True` in Python `print`:**  
   Python standard output by default buffer hota hai (line break aane tak hold karta hai).  
   `print(token, end="", flush=True)` buffer ko bypass karta hai aur terminal pe turant render karta hai.
2. **Windows UTF-8 Safe Console:**  
   Windows terminal default `cp1252` encoding pe crash ho jata hai jab emojis ya special symbols aate hain.  
   Hamesha `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` lagao.
3. **Type-Safe Dispatch:**  
   `isinstance(message, StreamEvent)` check karke hi `.event` padho.

### Complete Reference Code (`stream_runner.py`):

```python
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 1. Windows terminal encoding safety
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 2. Load environment variables
load_dotenv()

# 3. Import SDK modules
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent, ResultMessage


async def run_streaming_agent(prompt: str):
    """
    AC-01 Reference Implementation:
    Streams model output token-by-token with zero buffering.
    """
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,  # 👈 Critical for AC-01
        max_turns=1,
    )

    print(f"\n[USER PROMPT]: {prompt}\n")
    print("[CLAUDE STREAMING]: ", end="", flush=True)

    async for message in query(prompt=prompt, options=options):
        # Case 1: Live streaming token arrived
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                
                # Check for standard text output
                if delta.get("type") == "text_delta":
                    token = delta.get("text", "")
                    print(token, end="", flush=True)
                
                # Check for extended thinking reasoning (optional styling)
                elif delta.get("type") == "thinking_delta":
                    thought = delta.get("thinking", "")
                    # Dim grey output for reasoning
                    print(f"\033[90m{thought}\033[0m", end="", flush=True)

        # Case 2: Run completed successfully
        elif isinstance(message, ResultMessage):
            print("\n\n" + "-" * 50)
            print(f"✅ Run Completed | Subtype: {message.subtype}")
            print(f"⏱️  Duration    : {message.duration_ms / 1000:.2f}s")
            print(f"🔄 Turns       : {message.num_turns}")
            if message.total_cost_usd is not None:
                print(f"💰 Total Cost  : ${message.total_cost_usd:.4f}")
            print("-" * 50)


if __name__ == "__main__":
    prompt_text = "In 3 bullet points, explain why real-time streaming is critical for agentic user experience."
    asyncio.run(run_streaming_agent(prompt_text))
```

---

## 🎯 Part 5: Acceptance Criteria Checklist for AC-01

- [x] `include_partial_messages=True` is configured in `ClaudeAgentOptions`.
- [x] `StreamEvent` message types are caught and filtered.
- [x] `event["type"] == "content_block_delta"` with `delta["type"] == "text_delta"` is extracted.
- [x] Standard `print` uses `end=""` and `flush=True` for instant console rendering.
- [x] Zero buffer lag — user perceives immediate typing feedback.
- [x] Handles `SystemMessage`, `AssistantMessage`, and `ResultMessage` without `AttributeError`.

---

## 💡 Quick Recall Quiz (Test Your Understanding):

1. **Question:** `include_partial_messages=True` lagane par kaun sa naya message type yield hota hai?  
   **Answer:** `StreamEvent`.
2. **Question:** `message.event` direct har message pe kyun nahi call kar sakte?  
   **Answer:** Kyunki pehla message `SystemMessage` hota hai, jisme `.event` attribute exist nahi karta aur code crash ho jayega.
3. **Question:** Python ka default `print()` terminal pe token hold kyun kar leta hai?  
   **Answer:** Python ka stdout line-buffered hota hai. `flush=True` use karke hum buffer ko force flush karte hain.
