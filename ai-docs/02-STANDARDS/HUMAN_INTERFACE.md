# 🧠 Human Interface Guidelines (ADHD/INTP Optimized)

> **Goal**: Maximize information transfer with minimum cognitive load.

## 1. The "Golden Ratio" of Communication
*   **80% Logic / 20% Fluff**: Cut the polite "I hope you are doing well". Get to the point.
*   **Bottom Line Up Front (BLUF)**: State the result *first*, then the details.
    *   ❌ "After analyzing the logs... [10 lines] ... I found the error."
    *   ✅ "Found Error: Line 45 in `User_model.php`. Here is the analysis..."

## 2. Formatting for Scannability
*   **Bullet Points**: Use them everywhere. Avoid paragraphs > 3 lines.
*   **Bold Keywords**: Highlight **Variables**, **Paths**, and **Actions**.
*   **Code Blocks**: Use `backticks` for technical terms.

## 3. Decision Fatigue Management
*   **Don't ask "What do you want to do?"** (Too open-ended).
*   **Do propose "Option A vs Option B"**.
    *   **Option A**: Quick fix (Risk: High).
    *   **Option B**: Refactor (Time: 2 hours).

## 4. Short Codes (The User's API)
*   **ttt**: "Start Team" (Open Terminals).
*   **lll**: "Where are we? What's the context?" (Status Report).
*   **vvv**: "Did you check? Prove it." (Verification).
*   **nnn**: "What's the plan?" (Next Steps).
*   **gogogo**: "Execute." (Approval).
*   **rrr**: "What did we learn?" (Retrospective).

## 5. Handling Interruptions
*   If the user changes topics mid-task:
    1.  **Acknowledge** the new topic instantly.
    2.  **Tag** the old task: "Pausing [Task A]. Switching to [Task B]."
    3.  **Context Bookmark**: Save the state of Task A in `ai-docs/04-MEMORY/ACTIVE_CONTEXT.md` (if exists).
