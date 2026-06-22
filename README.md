# Agent Oculus

Agent Oculus is a small finance context worker.
It focuses on fast, readable context signals from:
- Public.com portfolio / market data
- WorldMonitor macro / regime data

## Install guide

Install Oculus as a Hermes profile:

```bash
hermes profile install . --name oculus --alias
```

Then use the installed profile:

```bash
oculus
```

Notes for fresh installs:

- If Hermes itself is not set up yet, run `hermes setup` and `hermes doctor` first.
- If you want the profile alias to work, keep `--alias` in the install command.
- When Oculus is installed as a Hermes profile, the Oculus profile model/provider defaults are the canonical path.
  
## Smoke test

For a quick check after install, open the profile and run a one-shot prompt from the normal Hermes command flow.

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
