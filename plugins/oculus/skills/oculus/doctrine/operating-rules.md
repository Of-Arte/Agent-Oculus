# Operating Rules

- When asked for market context, default to:
  1. portfolio snapshot
  2. macro context (regime + verdict)
  3. signal synthesis (alerts + IV analysis)
  4. summarize + list unknowns
- Always call out missing env vars / services directly
- If a service is unavailable, degrade gracefully and say so
- Prefer context signals over long narrative
- Surface what we know, what is missing, and what changed
