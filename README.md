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

2. Set the Hermes model/provider you want Oculus to use:

```bash
hermes model
```

3. Install Oculus as a Hermes profile and create the wrapper:

```bash
hermes profile install . --name oculus
hermes profile alias oculus
```

4. Start it:

```bash
oculus
```

Notes:
- If the profile comes up as `unknown`, rerun `hermes model` and save the desired provider/model first.
- If your normal Hermes default is Gemini Flash on AI Studio, set that before installing or relaunching Oculus.
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
