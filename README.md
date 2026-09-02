# Agent Oculus

Agent Oculus is an open-source financial context engine designed to provide fast, readable, and actionable market signals. It acts as a modular synthesis layer for financial data, enabling retail traders to monitor portfolios, track macro regimes, and build custom investment workflows using Hermes Agent.

## Core Capabilities

Agent Oculus provides structured financial signals to inform decision-making:

- **Portfolio Context:** Integrates with brokerage APIs to track real-time positions, buying power, and account health.
- **WorldMonitor Macro Intelligence:** Connects to WorldMonitor feeds to track global macro regimes, stablecoin peg stability, and critical supply chain chokepoints.
- **Volatility Analysis:** Real-time IV rank and percentile monitoring to identify high-volatility regimes.
- **Systematic Verdicts:** Synthesizes portfolio and macro data into structured JSON signals, offering regime classifications (e.g., TRANSITIONAL, HIGH_VOLATILITY) and IV analysis.
- **Safety-First Execution:** Designed for decision support; automated trading is strictly opt-in and disabled by default.

*Note: Oculus utilizes a fallback system that maintains visibility even when primary APIs are unavailable.*

## Quick Start

### 1. Install as a Hermes Profile
Install the project directly from the repository to set up a dedicated agent identity with its own memory, skills, and configuration.

```bash
hermes profile install https://github.com/Of-Arte/Agent-Oculus --name oculus --alias
```

### 2. Configure Your Environment
Copy the example environment file, then add your credentials and connect your WorldMonitor API endpoint:
```bash
cp ~/.hermes/profiles/oculus/.env.example ~/.hermes/profiles/oculus/.env
# Edit ~/.hermes/profiles/oculus/.env with your API keys:
# PUBLIC_API_SECRET_KEY=<your-public-secret-key>  WM_BASE_URL=...
```

**Getting your Public.com secret key:**

1. Go to https://public.com/settings/security/api and generate a secret key.
2. Set it as `PUBLIC_API_SECRET_KEY` in your `.env` file.
3. The agent will automatically exchange the secret key for a short-lived access token at runtime — you never need to manage access tokens manually.

**Setting up WorldMonitor:**

Agent Oculus connects to WorldMonitor for macro signals, stablecoin data, and supply chain intelligence.

1. Clone and start WorldMonitor from its repository: https://github.com/koala73/worldmonitor
2. Obtain an API key from your WorldMonitor instance (if authentication is enabled).
3. Set `WM_BASE_URL` in your `.env` file to your WorldMonitor instance URL.
4. If your WorldMonitor instance requires authentication, uncomment and set `WORLDMONITOR_API_KEY` in your `.env` file.

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
- `core/`: Core synthesis engines, API clients, schemas, and IV analysis.
- `plugins/oculus/`: Hermes plugin — toolpack (oculus_get_context, oculus_healthcheck), schema definitions, and bundled skill tree.
- `plugins/oculus/skills/oculus/`: Bundled skill (SKILL.md + refs + doctrine). This is the canonical skill tree.
- `config.yaml`: Runtime defaults and agent behavior settings.

## Architecture & Data Flow

The following sequence and object relationship diagram illustrates how data flows from the agent triggers, through external APIs, into the synthesis engine, and finally back to the agent as actionable intelligence.

```mermaid
flowchart TD
    %% Triggers
    Agent["Hermes Agent / CLI"] -->|"Invokes Tool"| ToolSignals["tools/get_signals.py"]

    %% Context Builder
    ToolSignals -->|"Initiates Build"| ContextBuilder["core/synthesis/context_builder.py"]

    %% API Clients
    subgraph External APIs
        WMClient["WorldMonitorClient (Macro/Sentiment)"]
        BrokerClient["PublicApiClient (Broker Data)"]
    end

    ContextBuilder -->|"Async Fetch"| WMClient
    ContextBuilder -->|"Async Fetch"| BrokerClient

    %% Synthesis Phase
    subgraph Synthesis Engine
        ContextBuilder -->|"1. Compute Volatility"| IVEngine["core/analytics/iv_rank.py"]
        ContextBuilder -->|"2. Detect Regime"| RegimeDetector["core/synthesis/regime_detector.py"]
        ContextBuilder -->|"3. Build Signals"| SignalNormalizer["core/synthesis/alert_engine.py"]
        ContextBuilder -->|"4. Evaluate Alerts"| AlertEngine["core/synthesis/alert_engine.py"]
    end

    %% Output
    IVEngine -.->|"Metrics"| FinanceContext["FinanceContext (core/schemas.py)"]
    RegimeDetector -.->|"RegimeResult"| FinanceContext
    SignalNormalizer -.->|"NormalizedSignals"| FinanceContext
    AlertEngine -.->|"Alerts"| FinanceContext

    FinanceContext -->|"Returned to Agent"| ToolSignals
```

### Class Relationships & Core Objects

The following class diagram outlines the design of the core services, API clients, and the unified `FinanceContext` data structure:

```mermaid
classDiagram
    direction LR

    class WorldMonitorClient {
        +base_url : str
        +api_key : str
        +request(method, path, params) dict
        +close()
    }

    class PublicApiClient {
        +base_url : str
        +access_token : str
        +request(method, path, params) dict
        +close()
    }

    class WorldMonitorMacroService {
        -client : WorldMonitorClient
        +get_macro_signals() MacroSignals
        +get_bis_policy_rates() list
        +get_energy_prices() EnergyPrices
    }

    class WorldMonitorMarketRadarService {
        -client : WorldMonitorClient
        +get_market_radar_verdict() MarketRadarVerdict
        +get_fear_greed() FearGreedIndex
    }

    class WorldMonitorStablecoinService {
        -client : WorldMonitorClient
        +list_stablecoin_markets() list
    }

    class PublicAccountService {
        -client : PublicApiClient
        +get_account_snapshot() AccountSnapshot
        +list_positions() list
    }

    class PublicOptionsService {
        -client : PublicApiClient
        +get_normalized_chain(symbol) OptionChain
    }

    class PublicMarketDataService {
        -client : PublicApiClient
        +get_quotes(symbols) dict
    }

    class FinanceContext {
        +account : AccountSnapshot
        +positions : list
        +quotes : dict
        +options_chains : dict
        +macro : MacroSignals
        +regime : str
        +regime_flags : list
        +signals : list
        +alerts : list
    }

    WorldMonitorMacroService --> WorldMonitorClient : Uses
    WorldMonitorMarketRadarService --> WorldMonitorClient : Uses
    WorldMonitorStablecoinService --> WorldMonitorClient : Uses

    PublicAccountService --> PublicApiClient : Uses
    PublicOptionsService --> PublicApiClient : Uses
    PublicMarketDataService --> PublicApiClient : Uses

    FinanceContext ..> WorldMonitorMacroService : Aggregates
    FinanceContext ..> PublicAccountService : Aggregates
```

## Safety & Disclaimer

- **Read-Only:** This profile is read-only — it synthesizes market context, portfolio data, and signal analysis only. No order execution tools are bundled.
- **Decision Support:** This project is designed for financial context synthesis and decision support. Automated trading logic (order placement, execution gating) exists only in the `automated-trading` branch and is not included in the default distribution.

## License
MIT
