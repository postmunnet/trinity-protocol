# What Is Trinity

Trinity is a governance kernel for AI-assisted work. It is not a new agent
framework and it is not a magic external brain.

```text
AI agent = worker
Trinity = control plane / supervisor
Artifact = evidence
Verifier = judge
Audit = black box recorder
Memory = artifact recall
Human = final authority
```

## What Problem It Solves

AI agents often say:

```text
I fixed it
It should pass
Looks good
```

Trinity pushes that into:

```text
There is a plan artifact
There is a diff
There is test output
There is a verifier verdict
There is an audit event
```

## Pyramid Of Judgment

```text
verifier rules -> policy gates -> LLM judge -> human
```

AI can advise and execute within scope. AI is not final authority.

## What Trinity Does Not Claim

- It does not guarantee correctness.
- It does not replace human deployment approval.
- It does not make production full-auto safe without gates.
- It does not let memory decide truth.

Trinity improves auditability, verification, and operational discipline.
