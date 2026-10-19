# 💰 AC-04 Master Tutorial: Financial Safeguards with `max_budget_usd`

> **Module:** Day 01 - Core Agent Execution Loop  
> **Topic:** Acceptance Criteria 04 (AC-04: Hard Cost Boundaries & Budget Enforcement)  
> **Language:** Hinglish (Desi Tech Breakdown) + Production Python Patterns  
> **Format:** Audio-Friendly / Read-Aloud Tutorial  

---

## 🎧 Part 1: The "Why" - Credit Card Bill Ka Darr!

Socho tumne ek SaaS company ka customer service agent banaya.  
Ek user ne achanak ek 500-page ki PDF upload karke agent ko prompt de diya:  
*"Compare every paragraph in this PDF with 10 other documents and write a 50,000-word analysis."*

Agar agent bina kisi financial limit ke chal raha hai:
- Input tokens: 500,000 tokens.
- Output tokens: 30,000 tokens.
- Single query ki cost ban gayi: **$10 se $15 (approx ₹800 - ₹1200)!**
- Agar aise 100 queries aa gaye, toh company ka hazaron rupaye ka nuksan ek ghante mein!

**Real-world Analogy:**  
Yeh waisa hi hai jaise tumne apne chhote bhai ko debit card diya shopping karne ke liye, lekin card pe **Daily Spending Limit set nahi ki!**  
Smart tareeqa kya hai? Card pe ₹500 ki limit laga do—jaise hi limit exceed ho, swipe decline ho jaye!

**AC-04 ka Goal:**  
SDK mein `max_budget_usd` set karna (e.g. `$0.01` ya `$0.05`).  
Jaise hi Claude ka cumulative token consumption us dollar amount ko touch kare, SDK query ko turant abort kar dega with status: **`error_max_budget_usd`**.

---

## ⚙️ Part 2: Under the Hood - Budget Checking Ka Mechanism

Claude Agent SDK budget kaise calculate karta hai?

```
[ Model API Call Complete ]
             │
             ▼
[ SDK calculates: (input_tokens * price) + (output_tokens * price) ]
             │
             ▼
[ Total Cost >= max_budget_usd ? ]
      │                     │
     YES                   NO
      │                     │
      ▼                     ▼
Emit ResultMessage       Next turn continues
subtype='error_max_budget_usd'
```

### Important Nuance (Interview Question ⭐):
SDK documentation mein ek bohot zaroori note likha hai:
> *"Budget checking happens after each API call completes, so the final cost may slightly exceed the specified budget by up to one API call's worth."*

**Matlab:** Agar tumne budget rakha `$0.001`, aur ek single turn ka kharcha `$0.0015` ho gaya, toh turn complete hone ke baad SDK check karega aur agla turn **block** kar dega. Isliye final cost budget se thodi si fractions-of-a-cent upar ho sakti hai, lekin runaway loop nahi chalega!

---

## 🛠️ Part 3: Production Code Pattern for AC-04

AC-04 ko verify karne ka sabse badhiya tareeqa hai:  
Agent ko ek aisi task do jo kam se kam 2-3 turns le, lekin budget ekdum tight rakh do (jaise `$0.0001` yaani a tiny fraction of a cent).  
Dekho agent kaise budget limit par halt hota hai!

```python
import os
import sys
import asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from claude_agent_sdk import query, ClaudeAgentOptions
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

    async for message in query(prompt=prompt, options=options):
        # Stream text live
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    print(delta.get("text", ""), end="", flush=True)

        # Check ResultMessage for budget violation
        elif isinstance(message, ResultMessage):
            print("\n" + "=" * 50)
            print("🛑 Run Terminated!")
            print(f"  Result Subtype : {message.subtype}")
            print(f"  Total Cost     : ${message.total_cost_usd or 0:.6f}")
            print("=" * 50)

            # AC-04 Verification:
            if message.subtype == "error_max_budget_usd":
                print("✅ AC-04 PASSED: Hard financial cap triggered successfully!")
                print("   Agent was cleanly stopped by SDK before burning money.")
            elif message.subtype == "success":
                print("ℹ️ Query finished within budget limits.")
            else:
                print(f"⚠️ Terminated with subtype: {message.subtype}")


if __name__ == "__main__":
    asyncio.run(run_budget_bounded_agent())
```

---

## 🎯 Part 4: Acceptance Criteria Checklist for AC-04

- [x] Configure `max_budget_usd` in `ClaudeAgentOptions`.
- [x] Catch `message.subtype == "error_max_budget_usd"` in `ResultMessage`.
- [x] Verify that execution halts immediately without continuing further turns.
- [x] Display total cost in USD with high decimal precision.

---

## 💡 Quick Recall Quiz:

1. **Question:** `max_budget_usd` kis currency mein calculate hota hai?  
   **Answer:** US Dollars (USD).
2. **Question:** Jab budget exceed hota hai toh Python koi exception fekta hai ya ResultMessage deta hai?  
   **Answer:** Python crash nahi hota! SDK gracefully ek `ResultMessage` deta hai jisme `subtype="error_max_budget_usd"` hota hai.
