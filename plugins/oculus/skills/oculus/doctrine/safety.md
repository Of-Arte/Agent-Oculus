# Safety

## Execution Gate

- `EXECUTION_ENABLED` defaults to `false`.
- Live order submission requires explicit user opt-in (`EXECUTION_ENABLED=true`).
- When execution is disabled, `place_order` raises `ExecutionDisabledError`.
- The agent must never suggest setting `EXECUTION_ENABLED=true` unless the user explicitly asks.

## Downside Management (v1)

- Hard stops only: close on downside breach.
- No rolling, no hedging (for initial implementation).

## Order Intent

- All trade suggestions are represented as `OrderRequest` objects for later use
  by automated trading tools (deferred to feat/automated-trading branch).
- The agent does not execute orders directly; it synthesizes context and order intent.

## LLM Capability

- The agent runs a lightweight LLM incapable of software-engineering tasks.
- Do not expose code-editing, repo-management, or file-system tools.
- Skills like `claude-code`, `codex`, `opencode`, `simplify-code`, `test-driven-development`
  are disabled by default in the profile config.
