# Agent Oculus

Agent Oculus is a small finance context worker.
It focuses on fast, readable context signals from:
- Public.com portfolio / market data
- WorldMonitor macro / regime data

## Quick start

Install Oculus as a Hermes profile:

```bash
hermes profile install . --name oculus --alias
```

Then launch the installed profile through Hermes:

```bash
hermes -p oculus
```

If you enabled the alias, you can also start it with `oculus`.

For a one-shot smoke test, run the profile through Hermes and use the same command flow you would in a real session.

For test/dev extras while developing the repo itself:

```bash
python -m pip install -e '.[dev]'
```

## First-time Hermes setup or sandbox smoke test

If you're setting up Hermes for the first time, use Hermes' built-in setup first:

```bash
hermes setup
hermes doctor
```

Then install Oculus as a profile and run it through Hermes:

```bash
hermes profile install . --name oculus --alias
hermes -p oculus
```

Notes:
- When Oculus is installed as a Hermes profile, the Oculus profile model/provider defaults are the canonical path.

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
