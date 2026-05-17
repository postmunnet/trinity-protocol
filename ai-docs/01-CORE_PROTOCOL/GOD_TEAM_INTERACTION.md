# God Team Interaction Protocol (Updated)

> 🔴 **Updated Rule**: Always use **Batch Send -> Sequential Poke** pattern.

## The Protocol

1.  **Batch Send**: Send the command (e.g., `lll`) to **ALL** agents first. Do not wait for one to finish before sending to the next.
2.  **Sequential Poke**: Once commands are sent, "Poke" (send `\n`) each agent one by one.
    - Order: Gemini 🟦 → Claude 🟧 → Codex ⬛

## Why?
- **Efficiency**: All agents start processing immediately.
- **Buffer Management**: The sequential poke ensures the tmux buffer refreshes and displays output correctly without freezing.

## Example (Tmux Command)
```bash
# 1. Batch Send
tmux send-keys -t ai-agents.1 "lll" C-m
tmux send-keys -t ai-agents.2 "lll" C-m
tmux send-keys -t ai-agents.3 "lll" C-m

# 2. Sequential Poke
sleep 2
tmux send-keys -t ai-agents.1 C-m
sleep 1
tmux send-keys -t ai-agents.2 C-m
sleep 1
tmux send-keys -t ai-agents.3 C-m
```
