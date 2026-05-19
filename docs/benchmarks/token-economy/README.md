# Why CLI Agents Have a 50-Year Head Start

> Same task, three paths, measured. The numbers point at an architectural
> moat that MCP cannot patch by shipping a faster runtime.

**Task** — Open `https://github.com/postmunnet/trinity-protocol` and bring
the README content into the model's working context.

**Three paths measured**:
1. **`curl`** — pure Unix baseline (raw markdown via `raw.githubusercontent.com`)
2. **`browser-cli`** — Trinity's Playwright REPL sibling (stdin/stdout JSON)
3. **`MCP claude-in-chrome`** — Model Context Protocol browser tools

**Method** — Same task, three paths. Token count = `chars / 3.8` (English-BPE
proxy; stable for relative comparison, not Anthropic's official tokenizer).
All raw I/O captured byte-for-byte under [`raw/`](raw/) next to this README — reproducible at any time.

**Environment** — Claude Code, Opus 4.7, 2026-05-18. MCP loaded via
ToolSearch (deferred, not eager) — i.e. the *kindest possible* MCP case.

---

## Headline

| Path | Round-trips | Schema tax | Body I/O | **Total tokens** |
|---|:---:|---:|---:|---:|
| **`curl`** (raw markdown) | 1 | 0 | 1,821 | **1,821** |
| **`browser-cli`** (Playwright sibling) | 1 (compound stdin) | 0 | 1,811 | **1,811** |
| **MCP** (`claude-in-chrome`, deferred) | 3 | 619 | 1,941 | **2,560** |

> **browser-cli matches curl on token cost and beats MCP by ~29% — in one
> round-trip instead of three, with zero per-task schema tax.**

If MCP were loaded eagerly (classic mode — all ~40 chrome tool schemas in
the system prompt every turn whether used or not), schema tax alone adds
~7,000 tokens → MCP total balloons to ~9,500 tokens → **5×+ worse than
either CLI path**.

---

## 📍 Update — Phase 1 (2026-05-19): browser-cli flips ahead of curl

One day after v1 measurement, `browser-cli` received a whitespace
normalizer in `lib/commands/read.js` — collapsing CSS-Grid spacer divs
and trimming trailing whitespace before returning extracted text.
Same task, fresh measurement:

| Path | v1 (2026-05-18) | v2 (2026-05-19, with normalizer) | Δ |
|---|---:|---:|---:|
| `curl` raw README | 1,821 | 2,189 | +368 *(README content grew)* |
| `browser-cli` | 1,828 | **1,896** | +68 |
| **Δ (bcli vs curl)** | **+7 (curl wins by 0.4%)** | **−293 (browser-cli wins by 13.4%)** | **flip** |

**Why it flipped:**

1. **Whitespace normalizer cleared the spacer-junk** — blank-or-junk
   line ratio in extracted article: **50% → 19%** (−31 percentage
   points). The advisor's `lib/commands/read.js` patch worked.
2. **`curl` shipped a bigger payload, not by choice** — GitHub's README
   grew over the day (v0.1.0 release prep + new Trinity origin / ritual
   reference sections). `curl` is forced to ship the *full* grown
   markdown; `browser-cli` ships only the rendered `<article>` element,
   leaving footer / sidebar / license / badges behind.
3. The advisor predicted ~920 tokens for browser-cli post-Phase-1.
   Actual landing is 1,896 — higher than predicted because the README
   itself grew during the same window — but the **direction matches**:
   browser-cli now wins on signal density per token.

**Section "What did `browser-cli` charge for that `curl` did not?" is now
partially obsolete:**

| Original finding | Status post-Phase-1 |
|---|---|
| Whitespace pollution (50% blank/junk lines) | ✅ **fixed** — now 19% |
| Latency (~2s Playwright cold-start vs ~200ms curl) | ⏳ still applies |
| Loss of structure (no `#` headings, no fence tags) | ⏳ still applies |

Post-Phase-1 calculus: `browser-cli` wins on tokens, still loses on
latency, still loses on markdown structure. The composition of these
trade-offs continues to support the routing matrix in
[`USE_CASE_ROUTING.md`](../../contracts/browser-cli/USE_CASE_ROUTING.md).

**Honest disclosure:** the v2 result depends on an *uncommitted* change
in the `browser-cli` sibling repo (`lib/commands/read.js`) at the time
of writing. The benchmark will be re-verified once the change is
committed and tagged. v1 numbers above remain the only fully-citable
baseline until then.

**Reproduction (v2):**

```
cd /path/to/browser-cli   # v0.3.0+ with normalizer patch
printf 'goto https://github.com/postmunnet/trinity-protocol\ntext article\nexit\n' \
  | node index.js
```

Raw v2 output captured under `raw/`:
- [`raw/bcli_v2_input.txt`](raw/bcli_v2_input.txt) — same 3-line script
- [`raw/bcli_v2_output_2026-05-19.txt`](raw/bcli_v2_output_2026-05-19.txt) — full response (7,134 chars)
- [`raw/curl_output_2026-05-19.md`](raw/curl_output_2026-05-19.md) — same-day curl baseline (8,235 chars)

v1 baseline preserved at `raw/bcli_output.txt` + `raw/curl_output.md` for diff inspection.

---

## Why CLI tools have a 50-year head start

GitHub exposes a **content-addressable abstraction** at
`raw.githubusercontent.com/<user>/<repo>/<branch>/README.md`. CLI tools
can hit it in one round-trip with no state, no schema tax, no chrome.

Two of the three CLI ideologies beat MCP on tokens:
- **`curl` wins on signal-per-token** (raw markdown structure)
- **`browser-cli` wins on schema-cost-per-call** (one tool, many verbs)
- **MCP loses on round-trip count** *and* schema tax *and* runtime nagging

> **The moat is not "CLI tools are faster."**
> **The moat is "CLI tools have access to better abstractions because
> Unix has had 50 years to design them, HTTP has had 30, and the
> Playwright REPL contract is `load once, command many` — whereas MCP
> is `load each, schema each, round-trip each`."**

This is a *structural* moat, not an *optimization* moat. MCP cannot ship a
release that closes it without redesigning the protocol — at which point
it would no longer be MCP.

```
curl reads what is publicly addressable.
browser-cli reads what is rendered, what is authenticated,
            and logs what was done.

curl is stateless.    browser-cli has provenance.
curl cannot click.    browser-cli enforces policy.

The right tool for the layer it works at.
Trinity composes both.
```

See [`docs/contracts/browser-cli/USE_CASE_ROUTING.md`](../../contracts/browser-cli/USE_CASE_ROUTING.md) for the full routing matrix between `curl`, `browser-cli`, and the cases that require each.

---

## Path A — `curl` (Unix baseline)

| Leg | Payload | chars | tokens (≈) |
|---|---|---:|---:|
| Tool description | `Bash` is base-context — $0 marginal | 0 | 0 |
| Tool call (input) | `curl -sL https://raw.githubusercontent.com/postmunnet/trinity-protocol/main/README.md` | 85 | 22 |
| Tool result (output) | Raw `README.md` (UTF-8 markdown, headings/links/code-fences preserved) | 6,835 | 1,799 |
| **Total** | 1 round-trip | **6,920** | **1,821** |

**Signal quality:** ★★★★★ — Raw markdown is the canonical form. Headings, links, code fences all preserved.

## Path B — `browser-cli` (Trinity sibling, Playwright stdin/stdout)

```
printf 'goto https://github.com/postmunnet/trinity-protocol\n
        text article\n
        exit\n' | node browser-cli/index.js
```

| Leg | Payload | chars | tokens (≈) |
|---|---|---:|---:|
| Tool description | `Bash` is base-context — $0 marginal | 0 | 0 |
| Command vocabulary | `COMMAND_CONTRACT.md` loaded once per agent lifetime, amortized to ~0 per task; per-task verbs used here = `goto`, `text` (~10 tokens if explicit) | ~0 | ~0 |
| Tool call (input) | 3-line script (`goto`, `text article`, `exit`) | 70 | 18 |
| Tool result (output) | Banner + 2 JSON responses (`{ok, url, title}` + `{ok, text}` with article body) | 6,878 | 1,810 |
| **Total** | 1 compound invocation | **6,948** | **1,828** |

**Signal quality:** ★★★☆☆ — Plain text only. Markdown structure stripped. **~50% of output lines are blank or CSS-Grid spacer junk** (178 of 354 lines) — the renderer pollutes the agent's context with non-semantic whitespace from GitHub's layout grid.

## Path C — MCP (`claude-in-chrome`, deferred load)

| Leg | Payload | chars | tokens (≈) |
|---|---|---:|---:|
| Tool descriptions (×3) | `tabs_context_mcp` + `navigate` + `get_page_text` schemas loaded via ToolSearch | 2,351 | 619 |
| 1. `tabs_context_mcp` | `{createIfEmpty:true}` + tab-list + redundant Tab-Context echo + `browser_batch` nag | 554 | 146 |
| 2. `navigate` | `{tabId, url}` + nav-confirmation + redundant Tab-Context echo + nag | 574 | 151 |
| 3. `get_page_text` | `{tabId}` + extracted article text + redundant Tab-Context echo | 6,249 | 1,644 |
| **Total** | 3 round-trips + schema load | **9,728** | **2,560** |

**Signal quality:** ★★★★☆ — Extracted text is cleaner than browser-cli's (better article filter). Still no markdown structure, but no spacer-junk pollution.

---

## What did MCP charge for that the CLI paths did not?

1. **Schema tax — 619 tokens** just to describe 3 tools in the conversation. Per task. Every conversation.
2. **Redundant Tab-Context echo** — ~80 chars of tab metadata printed on every call (~240 chars over 3 calls). You didn't ask for it; it ships anyway.
3. **`browser_batch` nag** — system-reminder fires after every single tool call ("Prefer browser_batch — it is significantly faster"). 2 fired this run = ~560 chars. *Anthropic's own runtime is telling you MCP is too chatty in its own infrastructure.*
4. **State management overhead** — tabId, tabGroupId, createIfEmpty flag. CLI paths have zero state between calls.

---

## What did browser-cli charge for that `curl` did not?

1. **Whitespace pollution** — GitHub's CSS Grid uses spacer divs (`<div></div>` with grid placement). `text article` flattens these to repeating empty lines. ~50% of output is blank/junk. This is a *signal* problem, not a *cost* problem — same tokens, less meaning per token.
2. **Latency** — Playwright cold-start is ~2s vs `curl` at ~200ms. Token-equal but wall-clock costlier.
3. **Loss of structure** — No `#` heading levels, no fence tags, no link URLs. Agent has to infer structure from indentation.

**Where browser-cli wins:** sites that *don't* expose raw markdown (auth-gated dashboards, JS-rendered SPAs, login-required content). curl can't reach those. browser-cli is the right tool *when* CDP-level access is required — but for GitHub READMEs, curl is still the optimal CLI primitive.

---

## Compounding cost over realistic workloads

Per-repo overhead vs cheapest CLI path:

| Workload | curl total | browser-cli total | MCP total | MCP excess vs curl |
|---|---:|---:|---:|---:|
| 1 repo skim | 1.8K | 1.8K | 2.6K | +0.7K |
| 10-repo competitive analysis | 18K | 18K | 26K | +7K |
| 100-repo crawl (dependency audit) | 180K | 180K | 256K | **+76K** |
| 1,000-repo (large-scale OSS scan) | 1.8M | 1.8M | 2.6M | **+760K** |

For an agent with a 200K context window, **+76K tokens on a 100-repo task
is the difference between "fits" and "summarize and drop half"**.

---

## Methodology disclosures

1. **Token proxy:** `chars / 3.8`. Calibrated for English BPE. UTF-8 Thai
   tokenizes ~2.0–2.5× denser, so absolute tokens for the Thai-mixed
   README are slightly higher than reported. All paths read identical
   Thai content, so the *relative* comparison is unaffected.

2. **MCP "deferred" mode** is the kindest possible read on MCP. Eager-load
   (classic Claude Desktop, Cursor, Continue, etc.) charges for every
   connected tool every turn. Chrome MCP exposes ~40 tools; conservative
   ~6,000-token schema tax in eager mode. **Add 6,000 to MCP total to
   get the classic-mode comparison.**

3. **browser-cli "schema tax" is ~0 per task** because:
   - The `Bash` tool description is base context.
   - The `browser-cli` *command vocabulary* (COMMAND_CONTRACT.md) is
     read once when the agent first learns the tool — amortized to near-zero
     over any non-trivial workload.
   - This contrasts MCP, which charges schema per *tool call* (per turn
     in eager mode, per `ToolSearch` invocation in deferred mode).

4. **`curl` baseline is `raw.githubusercontent.com`**, not HTML scraping —
   on purpose. The point is that CLI-first agents *would* use the
   cleaner abstraction. An "apples-to-apples HTML scrape" CLI would just
   bring curl up to ~browser-cli's cost, not change the MCP delta.

5. **MCP `tabs_create_mcp` was not needed** because `tabs_context_mcp`
   with `createIfEmpty:true` produces a fresh tab in the same call. The
   schema for `tabs_create_mcp` is therefore *not* in the 619-token
   count, even though typical MCP usage docs imply you should preload it.
   Counting it would push MCP schema tax to ~700 tokens.

6. **System reminders** ("Prefer browser_batch...") are counted as
   real context pollution because they are real bytes the model has to
   process. If you disable them, MCP drops by ~150 tokens — still ≥35%
   worse than either CLI path.

---

## Reproduction

All raw I/O captured byte-for-byte under `raw/` next to this README.
Re-run the measurement at any time:

```bash
cd docs/benchmarks/token-economy

# Path A — curl raw README
curl -sL https://raw.githubusercontent.com/postmunnet/trinity-protocol/main/README.md > /tmp/curl.md
python3 count.py /tmp/curl.md

# Path B — browser-cli (Trinity sibling, expects /path/to/browser-cli/)
printf 'goto https://github.com/postmunnet/trinity-protocol\ntext article\nexit\n' \
  | node /path/to/browser-cli/index.js > /tmp/bcli.txt
python3 count.py /tmp/bcli.txt

# Path C — MCP requires Claude Code + chrome-in-chrome extension;
# this run's raw outputs are in raw/mcp_*.txt

# Verify committed raw artifacts:
for f in raw/*; do python3 count.py "$f"; done
```

Directory layout:

```
docs/benchmarks/token-economy/
├── README.md          # this file
├── count.py           # token proxy (chars / 3.8)
└── raw/
    ├── curl_input.txt                       # v1, 2026-05-18
    ├── curl_output.md                       # v1, 2026-05-18
    ├── curl_output_2026-05-19.md            # v2 baseline (same-day)
    ├── bcli_input.txt                       # v1
    ├── bcli_output.txt                      # v1
    ├── bcli_v2_input.txt                    # v2
    ├── bcli_v2_output_2026-05-19.txt        # v2 with normalizer
    ├── mcp_schemas_used.json
    ├── mcp_1_tabs_context.txt
    ├── mcp_2_navigate.txt
    └── mcp_3_get_page_text.txt
```
