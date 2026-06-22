# Agent Oculus

Agent Oculus is an open-source financial context engine designed to provide fast, readable, and actionable market signals. It acts as a modular synthesis layer for financial data, enabling retail traders to monitor portfolios, track macro regimes, and build custom investment workflows using Hermes Agent.

## Core Capabilities

Agent Oculus provides structured financial signals to inform decision-making:

- **Portfolio Context:** Integrates with brokerage APIs to track real-time positions, buying power, and account health.
- **WorldMonitor Macro Intelligence:** Connects to WorldMonitor feeds to track global macro regimes, stablecoin peg stability, and critical supply chain chokepoints.
- **Volatility Analysis:** Real-time IV rank and percentile monitoring to identify high-volatility regimes.
- **Systematic Verdicts:** Synthesizes portfolio and macro data into structured JSON signals, offering regime classifications (e.g., TRANSITIONAL, HIGH_VOLATILITY) and strategy recommendations.
- **Safety-First Execution:** Designed for decision support; automated trading is strictly opt-in and disabled by default.

*Note: Oculus utilizes a fallback system that maintains visibility even when primary APIs are unavailable.*

## Quick Start

### 1. Install as a Hermes Profile
Install the project directly from the repository to set up a dedicated agent identity with its own memory, skills, and configuration.

```bash
hermes profile install https://github.com/Of-Arte/agent-oculus --name oculus --alias
```

### 2. Configure Your Environment
Copy the example environment file, then add your credentials and connect your WorldMonitor API endpoint:
```bash
cp ~/.hermes/profiles/oculus/.env.EXAMPLE ~/.hermes/profiles/oculus/.env
# Edit ~/.hermes/profiles/oculus/.env with your API keys:
# PUBLIC_ACCESS_TOKEN=*** WM_BASE_URL=...
```

### 3. Launch
Setup your API provider and your model of choice and launch the agent via the installed alias:
```bash
oculus model
oculus
```
**Important:** Always run the `oculus model` on a **fresh install** of Hermes Agent to avoid conflicts with API key configurations.

## Adding Your Own Integrations
Agent Oculus is built to be modified. To add a new data source or integration:

1. **Create a Tool:** Add a new script in `tools/` that fetches your desired data.
2. **Expose to Agent:** Register your tool in the `tools/` module.
3. **Synthesis:** Update `core/` to include the new signal in the agent's synthesis logic.

Because it is a Hermes profile, you can also install third-party Hermes plugins or MCP servers (`hermes mcp add`) to bring in external functionality without modifying the core repo.

## Project Structure
- `main.py`: CLI entry point and agent scheduler.
- `core/`: Core synthesis engines, analytics, and output formatting.
- `tools/`: Reusable integration modules for financial data.
- `skills/`: Reusable agentic procedures (see `hermes skills list`).
- `config.yaml`: Runtime defaults and agent behavior settings.

## Safety & Disclaimer
- **Default State:** Execution is disabled by default (`EXECUTION_ENABLED=false`).
- **Decision Support:** This project is designed for financial context synthesis and decision support. Do not enable automated trading logic until you have thoroughly tested your strategy within the sandbox.

## License
MIT
