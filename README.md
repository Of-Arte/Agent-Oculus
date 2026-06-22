# Agent Oculus

Agent Oculus is a small finance context worker.
It focuses on fast, readable context signals from:
- Public.com portfolio / market data
- WorldMonitor macro / regime data
- derived signals and alerts for downstream agents

The project is now centered on Hermes profile install + profile launch.
No skin layer. No theme setup. Use Hermes' normal profile flow.

## Quick start

Install Oculus as a Hermes profile:

```bash
hermes profile install . --alias oculus
```

Launch it through Hermes:

```bash
hermes -p oculus
```

For a one-shot smoke test, open that profile in Hermes and use the same command flow you would in a real session.

For test/dev extras while developing the repo itself:

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

After that, follow the quick start above.

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
