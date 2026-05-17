# Artifact Truth

Trinity's operating rule:

```text
No artifact = no trust
No verification = no completion
```

These claims are not enough:

```text
I fixed it
It should pass
No issue found
```

You need evidence:

```text
pytest output
diff/stat
verifier report
release evidence
audit event
export manifest
```

## Example Artifacts

- `THINK/plan_envelope.json`
- `THINK/02_SCOPE.md`
- `THINK/03_ACCEPTANCE.md`
- `CAPTURE/...`
- `docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`
- `EXPORT_MANIFEST.md` in the generated export

## Memory Is Not Truth

`memory-cli` is for search and recall over indexed artifacts.

```text
rrr -> memory-cli index <retro-path>
```

Not:

```text
rrr -> memory-cli learn
```

Memory retrieves; it does not judge.
