# Agent Oculus

Agent Oculus is a small finance context worker.
It focuses on fast, readable context signals from:
- Public.com portfolio / market data
- WorldMonitor macro / regime data

## Install guide

1. Run Hermes setup if needed:

```bash
hermes setup
hermes doctor
```

2. Install Oculus as a Hermes profile and create the wrapper:

```bash
hermes profile install . --name oculus
hermes profile alias oculus
```

3. Start it:

```bash
oculus
```

Notes:
- The profile ships with a default Gemini Flash model on Google AI Studio.
- If you want to change the profile model later, do it with `hermes model` after install.
- In a sandbox, use the normal Hermes profile flow instead of editing shell state by hand.

## Smoke test

After install, start `oculus` and send one short prompt to confirm the profile loads the expected model/provider.

## What you need

- `PUBLIC_ACCESS_TOKEN`
- `WM_BASE_URL`

Optional:
- `WORLDMONITOR_API_KEY`
- `EXECUTION_ENABLED=false` unless you explicitly want order execution logic enabled

## Project layout

- `main.py` — CLI runtime and scheduler
- `core/` — clients, analytics, synthesis, output formatting
- `tools/` — reusable entrypoints for portfolio, macro, and signals
- `SOUL.md` — repo mission / operating rules
- `config.yaml` — runtime defaults

## Safety model

- No live trading by default
- `EXECUTION_ENABLED` must stay `false` unless you explicitly change it
- The repo is designed for context generation and decision support, not unattended execution

## Tests

```bash
python -m pytest
```

## License

MIT
