#!/usr/bin/env python3
"""Token-count proxy for Claude-class tokenizers.

Method: chars / 3.8 (English/ASCII baseline, typical Claude/GPT BPE rate).
We report chars + estimated tokens side by side so any reader can audit.
Not a substitute for Anthropic's official count_tokens API, but stable
and adequate for relative comparison within one document corpus.
"""
import sys, json, pathlib

RATIO = 3.8

def measure(label: str, text: str):
    chars = len(text)
    tokens = round(chars / RATIO)
    return {"label": label, "chars": chars, "tokens_est": tokens}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # stdin mode
        text = sys.stdin.read()
        result = measure("stdin", text)
    else:
        path = pathlib.Path(sys.argv[1])
        text = path.read_text(encoding="utf-8", errors="replace")
        result = measure(path.name, text)
    print(json.dumps(result, ensure_ascii=False))
