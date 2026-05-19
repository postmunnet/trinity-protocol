# Use-Case Routing — `curl` vs `browser-cli` vs MCP

> Companion to [`docs/benchmarks/token-economy/`](../../benchmarks/token-economy/).
> The benchmark proves the token math; this doc explains *which tool fits
> which job* so the comparison isn't reductive ("just use curl").

`curl` is a primitive. `browser-cli` is a governed, observable, auth-aware
Playwright REPL. They occupy different layers — Trinity routes work to the
right layer.

---

## The matrix

| Situation                                              | Right tool                     | Why |
|---|---|---|
| Raw markdown / JSON / RSS / OpenGraph (content-addressable URLs) | `curl` *or* `browser-cli fetch` | No JS, no auth — the most primitive tool wins on tokens and latency |
| Auth-gated raw endpoint (logged-in API, admin JSON)    | `browser-cli fetch` (CDP mode) | Inherits cookies + CSRF from the user's browser context |
| Static HTML page (Wikipedia, blog, news article)       | `curl` + text extract          | Rendering unnecessary; HTML is already complete |
| JS-rendered SPA (React/Vue dashboard)                  | `browser-cli goto + text`      | `curl` only gets the shell HTML — content is hydrated client-side |
| Post-JS DOM state verification                         | `browser-cli`                  | `curl` cannot see DOM state after JavaScript runs |
| Human + AI hybrid workflow (demo → replay)             | `browser-cli` recorder         | `curl` has no session, no bidirectional action log |
| Verifier needs an action trace                         | `browser-cli` action-logger    | `curl` is a blackbox — no provenance, no audit |
| Policy-gated admin actions (`force-*` commands)        | `browser-cli` policy tier      | `curl` has no governance layer — every action is "tier high" by default |

---

## What `curl` actually is

`curl` is the canonical Unix primitive for "send an HTTP request and
print the body." 50 years of refinement. Zero state. Zero auth context.
Zero provenance. Zero clicks.

For content-addressable resources (raw GitHub files, JSON APIs without
auth, RSS feeds, OpenGraph metadata), `curl` is *unbeatable* on tokens,
latency, and operational simplicity. The token-economy benchmark
confirms this for the GitHub README case.

When you can use `curl`, use `curl`.

## What `browser-cli` actually is

`browser-cli` is a **governed, observable, auth-aware Playwright REPL**
exposed via stdin/stdout JSON. From the Trinity Tool Contract:

- **Action provenance** — every command is logged to NDJSON with
  `agent_name`, `verb`, `args`, `url`, `via`, `ts`. The verifier organ
  can answer "what did the AI actually do to this page?" — `curl`
  cannot.
- **Bidirectional recorder** — human clicks and AI commands are written
  to the same log, enabling "human demos → AI replays → verifier diffs"
  workflows.
- **CDP mode** — connect to a Chrome instance the user already has open.
  Cookies, extensions, and active sessions are inherited. The 50 lines
  of cookie-jar + CSRF management you'd write around `curl` collapse to
  one flag.
- **Policy tiers** — `safe` / `medium` / `high`. `force-*` commands are
  gated by the dispatch policy, not the agent's judgment.
- **YAML helpers** — composable, reusable workflows (`helpers/payment-check.yml`).
- **Built-in assertions** — `assert-text`, `assert-visible`, `assert-enabled`
  give you a verifier organ at the browser layer.

The token-economy benchmark shows `browser-cli` matches `curl` on cost
for a public README. The reason to reach for it is not cost — it's
**the four capabilities `curl` cannot provide**: auth context, JS state,
action provenance, governance.

## What MCP browser tools are not

MCP chrome tools occupy the same conceptual layer as `browser-cli` —
they automate a browser — but the protocol charges:

- **Schema tax per task** (~600 tokens for 3 tools in deferred mode;
  ~6,000+ in eager mode for the full chrome MCP).
- **Round-trip count** — every state read or write is a separate tool
  call; no native compound primitive.
- **Redundant Tab-Context echo** on every call.
- **No action provenance** at the protocol level — the trace lives in
  the agent's conversation log, not in a queryable artifact the
  verifier organ can inspect.

MCP can match `browser-cli` on raw browser capability. It cannot match
on **the structural moats** (single-pass invocation, append-only audit
log, content-addressable shortcuts, policy tiers as protocol — not as
agent self-discipline).

---

## How Trinity routes work between them

The kernel does not own this decision today — the agent picks. The
guidance:

```
if URL is content-addressable AND no auth needed:
    use curl
elif page is JS-rendered OR auth is required OR action trace matters:
    use browser-cli
else:
    use curl (defaults to the cheapest abstraction available)
```

A future `read <url> --prefer auto` meta-verb in `browser-cli` will
internalize this routing so that **`browser-cli` always uses the cheapest
abstraction available** — short-circuiting to HTTP when the URL is
content-addressable, falling back to Playwright when it isn't. That
collapses the agent-side decision tree to one verb, and turns the moat
into runnable code instead of a routing convention.

---

## See also

- [`docs/benchmarks/token-economy/`](../../benchmarks/token-economy/) — measurements
- [`docs/contracts/browser-cli/COMMAND_CONTRACT.md`](COMMAND_CONTRACT.md) — full verb inventory
- [`docs/contracts/browser-cli/POLICY_TIERS.md`](POLICY_TIERS.md) — tier mapping
- [`docs/contracts/browser-cli/AI_AGENT_GUIDE.md`](AI_AGENT_GUIDE.md) — agent invocation patterns
