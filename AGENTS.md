# AGENTS.md

> Development guide for the agent-oculus repository.

## Commit template

```
<scope>: <short summary>

[optional body - up to ~72 chars per line]

- Bullet list of changes if multiple

Verified:
- <verification step 1>
- <verification step 2>
```

### Scope conventions
- `v0.3.0` or `v<next>` — profile distribution version release commits
- `plugin` — plugins/ changes
- `skills` — bundled skills under plugins/oculus/skills/ changes
- `config` — config.yaml, distribution.yaml, VERSION, SOUL.md, AGENT_IDENTITY.md changes
- `core` — core/ changes
- `docs` — README.md, AGENTS.md, documentation-only changes
- `chore` — repo maintenance (gitignore, pyproject, file moves, tools/ removal)

### Version tracking
- **VERSION** (top-level): single version number, single source of truth
- **distribution.yaml**: version must match VERSION
- **plugin.yaml**: version must match VERSION
- **SKILL.md** frontmatter: version must match VERSION
- Bump all four together on release commits

### Per-phase commit discipline
Each phase of a multi-phase refactor gets its own commit. Never bundle two phases in one commit.

## Verification steps
- Syntax check: `python -m py_compile plugins/oculus/__init__.py plugins/oculus/tools.py plugins/oculus/schemas.py core/synthesis/context_orchestrator.py core/_version.py`
- Plugin discovery: `hermes profile install . --name oculus-test --alias --force -y` (in fresh HERMES_HOME)
- Skill loading: `hermes -p oculus-test skills list`
- Tool listing: `hermes -p oculus-test tools list`
- Core tests: `python -m pytest tests/ -q`

## Development workflow
1. Edit files in the repo
2. Run syntax checks + pytest
3. Reinstall profile: `hermes profile install . --name oculus --alias --force -y`
4. Verify plugin tools and skills appear
5. Test: `oculus chat -q "run healthcheck"`
