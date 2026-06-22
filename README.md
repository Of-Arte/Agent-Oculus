# Agent Oculus

Agent Oculus is a small finance context worker.
It focuses on fast, readable context signals from:
- Public.com portfolio / market data
- WorldMonitor macro / regime data
- derived signals and alerts for downstream agents

The project is now centered on a simple runtime first.
No skin layer. No profile-theme setup. Just install and run.

## Quick start

```bash
python -m pip install -e .
python main.py --run-once
```

If you want the continuous signal loop instead:

```bash
python main.py
```

For test/dev extras:

```bash
python -m pip install -e '.[dev]'
```

## What you need

- `PUBLIC_ACCESS_TOKEN`
- `WM_BASE_URL`

Optional:
- `WORLDMONITOR_API_KEY`
- `EXECUTION_ENABLED=false` unless you explicitly want order execution logic enabled

## What it prints

The one-shot mode prints a JSON config summary and a `CONTEXT_SIGNALS` block
with the current regime, signal list, and alerts.

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
