# 🔄 AC-03 Master Tutorial: Execution Loop Bounds with `max_turns`

> **Module:** Day 01 - Core Agent Execution Loop  
> **Topic:** Acceptance Criteria 03 (AC-03: Max Turns & Loop Safety)  
> **Language:** Hinglish (Desi Tech Breakdown) + Production Python Patterns  
> **Format:** Audio-Friendly / Read-Aloud Tutorial  

---

## 🎧 Part 1: The "Why" - Infinite Loop Problem Kya Hai?

Agentic systems aur normal chatbots mein sabse bada difference hota hai: **The ReAct Loop (Reason + Act)**.

```
Model Sochta hai (Reason) ──> Tool Call karta hai (Act) ──> Output wapas Model ke paas aata hai (Observe)
            ▲                                                                    │
            └────────────────────────────────────────────────────────────────────┘
```

### Jab Agent Pagal (Infinite Loop) Ho Jata Hai:
Socho tumne agent ko bola:  
*"Find `database_creds.env`. If it does not exist, keep checking other folders, rename files if needed, and do not stop until you find it."*

Ab agar wo file database mein exist hi nahi karti:
1. **Turn 1:** Agent ne `Glob` chalaya $\rightarrow$ File nahi mili.
2. **Turn 2:** Agent ne socha: *"Shayad kisi subfolder mein ho"*, firse `Glob` chalaya $\rightarrow$ Nahi mili.
3. **Turn 3:** Agent ne socha: *"Shayad hidden file ho"*, `Bash` command chalayi $\rightarrow$ Nahi mili.
4. **Turn 40:** Agent abhi bhi search kar raha hai...

**Khatra:**
- 10 minute mein agent 50 turns le lega.
- Har turn mein purani saari conversation context window mein judti jaati hai (Context window explosion).
- 50 turns = Lakhon tokens = Tumhare card se paise deduct!

**AC-03 ka Goal:**  
Humein ek **hard ceiling (chhat)** lagani hai: `max_turns=N`.  
Chahe task poora hua ho ya na hua ho, jaise hi `N` turns complete honge, system gracefully ruk jana chahiye bina crash kiye (Clean Exit Code 0).

---

## ⚙️ Part 2: SDK ke Andar `max_turns` Kaam Kaise Karta Hai?

Jab hum `ClaudeAgentOptions` configure karte hain:

```python
options = ClaudeAgentOptions(
    max_turns=2  # 👈 2 turns ke baad stop
)
```

### Turn ki Definition kya hai?
Ek "Turn" ka matlab hota hai:
- Model ka response aana (chahe wo text ho ya tool call).
- Agar model tool call karta hai, toh tool run hokar result wapas model tak jaana aur model ka dobara bolna = **Turn 2**.

### Jab `max_turns` Hit Hota Hai Toh Kya Milta Hai?
Jab limit reach hoti hai:
1. Subprocess crash nahi hota. Koi Python exception nahi aati.
2. SDK stream ke end mein ek **`ResultMessage`** emit karta hai:
   ```python
   ResultMessage(
       subtype="error_max_turns",  # ya normal termination with stop_reason
       num_turns=2,                # Exactly 2 par halt hua
       is_error=False / True,
       result="..."
   )
   ```

---

## 🛠️ Part 3: Production Code Pattern for AC-03

Chalo ek test code dekhte hain jisme hum agent ko ek cyclic task denge, lekin `max_turns=2` usko rukne par majboor karega.

```python
import os
import sys
import asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent, AssistantMessage, ToolUseBlock, ResultMessage


async def run_bounded_turns_agent():
    # AC-03: Hard limit of 2 turns
    options = ClaudeAgentOptions(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        include_partial_messages=True,
        allowed_tools=["Glob"],
        permission_mode="default",
        max_turns=2  # 👈 Hard Cap!
    )

    # Prompt designed to trigger multiple steps
    prompt = "Find all .txt files. Then find all .json files. Then find all .md files. Report each list step by step."

    print(f"🎯 Target max_turns: 2")
    print(f"👤 User: {prompt}\n")

    current_turns = 0

    async for message in query(prompt=prompt, options=options):
        # 1. Stream text deltas
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    print(delta.get("text", ""), end="", flush=True)

        # 2. Tool calls
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"\n🛠️  [Turn Action]: Tool '{block.name}' called with {block.input}")

        # 3. Final ResultMessage
        elif isinstance(message, ResultMessage):
            print("\n" + "=" * 50)
            print(f"🛑 Run Finished!")
            print(f"  Status Subtype : {message.subtype}")
            print(f"  Turns Consumed : {message.num_turns}")
            print(f"  Stop Reason    : {message.stop_reason}")
            print("=" * 50)
            
            # AC-03 Assertion:
            if message.num_turns <= 2:
                print("✅ AC-03 PASSED: Agent respected max_turns boundary!")
            else:
                print("❌ AC-03 FAILED: Agent exceeded turn limits!")


if __name__ == "__main__":
    asyncio.run(run_bounded_turns_agent())
```

---

## 🎯 Part 4: Acceptance Criteria Checklist for AC-03

- [x] Configure `max_turns=N` inside `ClaudeAgentOptions`.
- [x] Confirm that agent stops executing when `num_turns == N`.
- [x] Verify that script terminates with exit code 0 (no unhandled exceptions).
- [x] Inspect `message.num_turns` in `ResultMessage` to prove boundary enforcement.

---

## 💡 Quick Recall Quiz:

1. **Question:** Agar `max_turns` set na karein toh kya default unlimited hota hai?  
   **Answer:** CLI ke paas internal default limits hoti hain, lekin production mein kabhi default par bharosa nahi karte—hamesha explicit `max_turns` pass karna safe engineering practice hai.
2. **Question:** Agar agent ko 10 files inspect karni hain aur `max_turns=2` set kar dein toh kya hoga?  
   **Answer:** Agent pehli 1-2 files inspect karke stop ho jayega aur jitna kaam hua hai uska partial report de dega, bina hang hue.
