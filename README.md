# Agent Oculus (agent-oculus)

Agent Oculus is a Hermes-native finance context worker.
It pulls:
- portfolio / account context from Public.com
- macro / regime context from WorldMonitor
- derived signals suitable for downstream agent decisions

This repo is now structured as a Hermes profile distribution first.
That means the canonical install path is Hermes-native, not shell copy scripts.

---

## Hermes-native install

Use this when you want the project to show up as a Hermes profile with its own
assets, alias, skin, and plugin/tool surface.

```bash
git clone https://github.com/Of-Arte/agent-oculus.git
cd agent-oculus
hermes profile install . --alias
```

What that gives you:
- a dedicated `oculus` Hermes profile
- an `oculus` shell command alias managed by Hermes
- the Oculus skill
- the Oculus plugin/toolpack
- the Oculus skin
- the default profile config wired for the Oculus skin and plugin

After install:

```bash
oculus
```

Inside the profile, use the built-in tools and commands Hermes exposes.
The plugin is named `oculus` and the CLI skin is `oculus`.

If you want to install from a remote repo instead of a local checkout, use the same command with the repo URL.

---

## What’s included

Hermes profile assets:
- `SOUL.md` — profile identity / scope
- `config.yaml` — defaults, including skin + plugin enablement
- `skills/oculus/SKILL.md` — scope lock / intent mapping
- `plugins/oculus/` — Hermes toolpack
- `skins/oculus.yaml` — CLI skin/theme

Standalone runtime:
- `main.py` — one-shot or scheduled context worker
- `core/` — clients, analytics, synthesis, output formatting
- `tools/` — standalone Python entrypoints used by `main.py`

---

## Standalone Python install

Use this if you want to run the worker directly outside Hermes.

### Install

```bash
python -m pip install -e '.[dev]'
```

### Run once

```bash
python main.py --run-once
```

### Run the scheduler

```bash
python main.py
```

The one-shot mode prints JSON blocks for:
- `PORTFOLIO_SNAPSHOT`
- `MACRO_CONTEXT`
- `RUN_ONCE_RESULT`

---

## Configuration

Hermes profile configuration lives in `config.yaml` / `.env` under the profile home.
The project expects:
- `PUBLIC_ACCESS_TOKEN`
- `WM_BASE_URL`

Execution stays off by default.

---

## Safety model

- No live trading by default
- `EXECUTION_ENABLED` must remain `false` unless the user explicitly changes it
- The repo is designed for context generation and decision support, not unattended execution

---

## Tests

```bash
python -m pytest
```

---

## License

MIT
