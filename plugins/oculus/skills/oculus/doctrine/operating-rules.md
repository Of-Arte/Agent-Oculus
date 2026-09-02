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
- For SPX Jade Lizard contexts: $100–$500 max risk framing, 25% profit target, hard stops only (close on downside breach)
- Max 1 concurrent position under active consideration
- Market hours context: 10am–4pm ET (reference only; signals flow async)
