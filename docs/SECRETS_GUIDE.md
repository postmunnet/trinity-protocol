# Secrets Guide (v0.5)

This guide explains how to use the local secrets vault for demos and development.

## Overview

Trinity includes a minimal local vault stored under `.ai/.secrets/` for storing
secrets outside of your codebase. It is intended for local/dev use only.

## Commands

```bash
# Set a secret
ai vault set API_TOKEN "my-token-value"

# Retrieve a secret
ai vault get API_TOKEN

# List stored keys
ai vault list

# Delete a secret
ai vault delete API_TOKEN
```

## Best Practices

- Never hardcode secrets in code — use the vault, env vars, or proper secret managers.
- Add `.ai/.secrets/` to .gitignore (already configured) so secrets are not committed.
- For production, integrate a dedicated KMS/secret manager.

## How it works (brief)

- A random master key is generated at `.ai/.secrets/master.key` on first use.
- Each secret is stored as JSON with a per-entry nonce and XOR keystream derived via HMAC‑SHA256.
- This is demo‑grade confidentiality; replace with a production solution for real deployments.

