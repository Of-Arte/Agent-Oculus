# Safety

## Read-Only Profile

- This profile is read-only — no order execution tools are bundled or enabled.
- All data fetching uses non-mutating (GET) requests only.
- Automated trading logic (order placement, execution gating, downside management)
  lives in the `automated-trading` branch and is not included in this distribution.

## LLM Capability

- The agent runs a lightweight LLM incapable of software-engineering tasks.
- Do not expose code-editing, repo-management, or file-system tools.
- Skills like `claude-code`, `codex`, `opencode`, `simplify-code`, `test-driven-development`
  are disabled by default in the profile config.
