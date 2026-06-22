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

## First-time Hermes setup or sandbox smoke test

If you're setting up Hermes for the first time, use Hermes' built-in setup and model selection first:

```bash
hermes setup
hermes doctor
hermes model
```

Then run Oculus from the repo root with the normal command execution path:

```bash
python main.py --run-once
```

Notes:
- If you're testing inside a sandbox shell, prefer the existing Hermes command flow above instead of hand-editing the shell environment.
- When Oculus is installed as a Hermes profile, the Oculus profile model/provider defaults are the canonical path.
- Only change the model/provider manually when you're intentionally testing a different runtime or sandbox.

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
