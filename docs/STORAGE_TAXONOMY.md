# Storage Taxonomy

Trinity separates durable truth from temporary noise.

| Store | Purpose | Durability |
| --- | --- | --- |
| `.ai/audit/events.ndjson` | Hash-chain log of truth-changing events | Durable |
| `.ai/sessions/<id>/` | Session capsule for one task | Durable until archived/closed |
| `.ai/sessions/<id>/CAPTURE/` | Captured inputs, outputs, evidence | Durable evidence |
| `.ai/sessions/<id>/.state/` | Runtime pointers and markers | Durable pointer, not source of truth |
| `.ai/memory/` or sibling memory DB | Search/index over accepted artifacts | Rebuildable index |
| `/private/tmp/...github_export...` | Generated export packages | Disposable |

## Working Rule

```text
Audit = truth
Capture = evidence
State = pointer
Retro = learning artifact
Memory DB = index
Trace/tmp = disposable
```

Log everything that changes truth. Hash or capture what proves truth. Index
only artifacts that survived verification. Expire what is merely operational
noise.

## State Naming

`graph_state` is the canonical ritual state:

```text
READY -> THINK -> SANDBOX -> DO -> VERIFIED -> PROMOTED -> DEPLOYED -> RETRO -> DONE
```

`legacy_state` exists for older MVP lifecycle compatibility. New code should
not write an ambiguous top-level `state` field.
