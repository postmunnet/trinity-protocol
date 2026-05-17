# 🛠️ AI Tool Usage Protocol

> **Principle**: Tools are your eyes and hands. Use them precisely.

## 1. The "Blindness" Prevention (Ls & Find)
*   **Problem**: You cannot see the file tree unless you look.
*   **Rule**: Never guess a path. Always `ls` or `find`.
*   **Command**: `find . -maxdepth 3 -not -path '*/.*' | grep "partial_name"`

## 2. The "Hallucination" Prevention (Grep)
*   **Problem**: You think a function `getUserById` exists, but it's actually `get_user_by_id`.
*   **Rule**: Grep usage is mandatory before importing/calling.
*   **Command**: `grep -r "function get_user_by_id" {{APP_DIR}}/`

## 3. Large File Handling (Cat vs Head)
*   **Problem**: `cat huge_file.log` floods the context window.
*   **Rule**: Read large files in chunks.
*   **Command**: `tail -n 50 {{APP_DIR}}/logs/log-2025-12-18.php`

## 4. Git Best Practices
*   **Check Status**: `git status` (Always check before `gogogo`).
*   **Diff Check**: `git diff --stat` (See what changed).
*   **Safe Push**: Never `git push -f`.

## 5. Agent Mode Triggering
*   **Claude (`--introspect`)**: Use for complex debugging requiring reasoning.
*   **Gemini (`--analyze`)**: Use for high-level architecture reviews.
*   **Codex (`/codex-generate`)**: Use for generating boilerplate or refactoring.
