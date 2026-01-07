# Data Science with Multiple Agents

## Overview

This project demonstrates an intelligent multi-agent system designed for data retrieval and analysis. It features a root orchestrator that intelligently routes queries to specialized sub-agents based on user intent. The system connects to various data sources through MCP (Model Context Protocol) servers and provides both raw data access and advanced analytical visualizations.

The agent automatically determines whether you need simple data retrieval or complex analysis with charts, metrics, and insights - all through natural language queries.

## Agent Details
The key features of the Data Science Multi-Agent include:

| Feature | Description |
| --- | --- |
| **Interaction Type:** | Conversational |
| **Agent Type:**  | Multi-Agent (Root Orchestrator + Sub-Agents) |
| **Components:**  | MCP Server Integration, Intelligent Routing, Structured Output |
| **Data Sources:** | PostgreSQL, MSSQL, HubSpot, OpenMetadata (via MCP) |
| **Model Support:** | DeepSeek, Self-Hosted LLMs (vLLM) |

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│              ROOT ORCHESTRATOR AGENT                    │
│ • Analyzes user intent (retrieve vs analyze)            │
│ • Routes to appropriate sub-agents                      │
│ • Manages session state and context                     │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                     ┌────────────────┐
                     │  User Intent?  │
                     └────────────────┘
                       │           │
            ┌──────────┘           └──────────┐
            ▼                                 ▼
  ┌──────────────────┐             ┌──────────────────┐
  │  RETRIEVAL AGENT │             │  RETRIEVAL AGENT │
  │ • Connects to    │             │ • Fetches data   │
  │   MCP servers    │             │ • Passes data to │
  │ • Executes       │             │   Analytics Agent│
  │   queries        │             └──────────────────┘
  │ • Returns plain  │                        │
  │   text data      │                        ▼
  └──────────────────┘             ┌──────────────────┐
                                   │  ANALYTICS AGENT │
                                   │ • Analyzes data  │
                                   │ • Creates charts │
                                   │ • Generates JSON │
                                   └──────────────────┘
```
### Agent Components

#### 1. Root Orchestrator Agent
- **Purpose:** Intelligent query routing and orchestration
- **Capabilities:**
  - Classifies user intent automatically (retrieve vs analyze)
  - Manages conversation flow and context
  - Routes queries to appropriate sub-agents
  - Coordinates multi-step workflows

#### 2. Data Retrieval Agent
- **Purpose:** Fetch data from various sources via MCP
- **Capabilities:**
  - Connects to PostgreSQL, MSSQL databases
  - Integrates with HubSpot CRM
  - Accesses OpenMetadata catalog
  - Executes SQL queries and API calls
  - Returns formatted data tables
  - Stores raw data in session state for analytics

#### 3. Data Analytics Agent
- **Purpose:** Analyze data and create visualizations
- **Capabilities:**
  - Processes retrieved data from session state
  - Generates chart configurations (line, bar, pie, scatter, area, heatmap)
  - Calculates metrics and statistics
  - Provides data-driven insights
  - Creates actionable recommendations
  - Outputs structured JSON for UI rendering

### Key Features

*   **Intelligent Intent Classification:** Automatically determines if you want raw data or analysis
*   **Multi-Agent Architecture:** Root orchestrator coordinates specialized sub-agents for optimal performance
*   **MCP Server Integration:** Seamless connection to multiple data sources through Model Context Protocol
*   **Flexible Data Retrieval:** Query databases, APIs, and metadata catalogs using natural language
*   **Advanced Analytics:** Automatic chart generation, statistical analysis, and insight extraction
*   **Structured Outputs:** Analytics agent produces UI-ready JSON for direct chart rendering
*   **Context Management:** Session state maintains data flow between agents
*   **Multi-Model Support:** Works with DeepSeek, or self-hosted LLMs via vLLM

### Use Cases

- **Simple Queries:** "List all tables in the database" → Returns formatted table list
- **Data Exploration:** "Show me customer records from California" → Returns data table
- **Trend Analysis:** "Analyze sales trends over the last quarter" → Returns line chart with insights
- **Comparisons:** "Compare revenue by region" → Returns bar chart with metrics
- **Distributions:** "Show product sales distribution" → Returns pie chart with percentages
- **Complex Analysis:** "What's the correlation between price and sales volume?" → Returns scatter plot with statistical analysis

## Agent Setup and Installation

### Prerequisites

*   **LLM Configuration:** Choose one of the following options:
    - **DeepSeek API key** ([Get one here](https://platform.deepseek.com/)), OR
    - **Self-Hosted LLM** via vLLM (Mistral, Llama, etc.)
*   **Python 3.12+:** Ensure you have Python 3.12 or later installed
*   **uv:** Install uv package manager:
```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
```
Or follow instructions at [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
*   **Git:** Install from [https://git-scm.com/](https://git-scm.com/)
*   **MCP Servers:** Ensure your MCP servers are running and accessible


### ADK Project Setup with uv

1.  **Clone the Repository:**
```bash
    git clone https://github.com/sanjog-lama/data-science-agent.git
    cd data-science-agent
```

2.  **Install Dependencies with uv:**
```bash
    uv sync
```
This command reads the `pyproject.toml` file and installs all necessary dependencies into a virtual environment managed by uv. On the first run, this creates a new virtual environment in `.venv`.

3.  **Activate the uv Shell:**
```bash
    source .venv/bin/activate
```

4.  **Set up Environment Variables:**

    Create a `.env` file from the example:
```bash
    cp .env.example .env
```

Edit `.env` and configure your model backend (choose ONE option):

**Option 1: DeepSeek**
```bash
    MODEL_TYPE=deepseek
    DEEPSEEK_API_KEY='your-deepseek-api-key-here'
```

**Option 2: Self-Hosted LLM (vLLM)**
```bash
    MODEL_TYPE=vllm
    VLLM_MODEL_NAME='mistral-large:123b'
    VLLM_BASE_URL='http://localhost:9000/v1'
    VLLM_API_KEY='EMPTY'
```

**MCP Server Configuration (Required for all options):**
```bash
    MCP_SERVERS_JSON='[{"url":"http://localhost:8080/mcp"},{"url":"http://localhost:8081/mcp","auth":"true"}]'
    
    # If using authenticated MCP servers (auth: true)
    MCP_AUTH_TOKEN='your-mcp-auth-token'
    MCP_AUTH_SCHEME='Bearer'
```

## Model Configuration Details

### Supported LLM Backends

| Backend | MODEL_TYPE | Required Variables | Description |
|---------|------------|-------------------|-------------|
| **DeepSeek** | `deepseek` | `DEEPSEEK_API_KEY` | Cost-effective, powerful reasoning |
| **vLLM (Self-Hosted)** | `vllm` | `VLLM_BASE_URL`, `VLLM_MODEL_NAME` | Full control, privacy, no API costs |

### vLLM Self-Hosted Setup

If you're running your own LLM via vLLM:

1. **Start your vLLM server:**
```bash
   vllm serve mistral-large:123b --host 0.0.0.0 --port 9000
```

2. **Configure environment variables:**
```bash
   MODEL_TYPE=vllm
   VLLM_MODEL_NAME='mistral-large:123b'  # Your model name
   VLLM_BASE_URL='http://localhost:9000/v1'
   VLLM_API_KEY='EMPTY'  # Most local deployments don't need auth
```

## MCP Server Configuration

The agent connects to data sources via MCP (Model Context Protocol) servers. Configure the `MCP_SERVERS_JSON` environment variable with your server details.

See `.env.example` for a complete configuration template.

## Running the Agent

You can run the agent using ADK commands from your terminal.

### Option 1: CLI Mode (Terminal)
```bash
uv run adk run data_science
```

This launches an interactive terminal session where you can chat with the agent.

### Option 2: Web UI Mode
```bash
uv run adk web
```

Then:
1. Open your browser to the provided URL (usually `http://localhost:8000`)
2. Select `data_science` from the agent dropdown
3. Start chatting with the agent

## Project Structure
```
data_science/
├── agent.py                # Root orchestrator agent
├── prompts.py              # Agent instructions
├── tools.py                # MCP server integration utilities
├── __init__.py
└── sub_agents/
    ├── retrieval/
    │   ├── agent.py        # Data retrieval agent
    │   ├── prompts.py      # Retrieval instructions
    │   └── __init__.py
    └── analytics/
        ├── agent.py        # Analytics agent with structured output
        ├── prompts.py      # Analytics instructions
        └── __init__.py
```

## Optimization and Customization Tips

### 1. Prompt Engineering

Refine agent prompts to improve performance:
- **Root Agent:** Adjust intent classification keywords in `data_science/prompts.py`
- **Retrieval Agent:** Customize data formatting in `sub_agents/retrieval/prompts.py`
- **Analytics Agent:** Fine-tune chart selection logic in `sub_agents/analytics/prompts.py`

### 3. Adding New MCP Data Sources

Add new MCP servers to `MCP_SERVERS_JSON`:
```bash
# Add MongoDB MCP server
MCP_SERVERS_JSON='[
  {"url":"http://localhost:8080/mcp","auth":"false"},
  {"url":"http://localhost:8082/mcp","auth":"true"}
]'
```

Update `tools.py` to handle the new server type if needed.

### 3. Extending the Agent System

Add new sub-agents for specialized tasks:
```python
# In data_science/agent.py
from .sub_agents.forecasting.agent import get_forecasting_agent

forecasting_agent = get_forecasting_agent(model_config)
forecasting_tool = AgentTool(agent=forecasting_agent)

agent = LlmAgent(
    tools=[retrieval_tool, analytics_tool, forecasting_tool],
    sub_agents=[retrieval_agent, analytics_agent, forecasting_agent]
)
```
## Troubleshooting

### Common Issues

**Issue:** Model connection fails
- **Solution:** 
  - For vLLM: Check that your vLLM server is running at `VLLM_BASE_URL`
  - For DeepSeek: Verify `DEEPSEEK_API_KEY` is valid

**Issue:** MCP server connection fails
- **Solution:** 
  - Verify MCP servers are running and accessible
  - Check URLs in `MCP_SERVERS_JSON` are correct
  - For authenticated servers, ensure `MCP_AUTH_TOKEN` is set

## Support

For issues and questions:
- GitHub Issues: [Repo URL](https://github.com/sanjog-lama/data-science-agent)
- Documentation: [Doc](https://github.com/sanjog-lama/data-science-agent/README.md)
- Email: [sanjog.gomden@berrybytes.com]

---

**Built with Google ADK (Agent Development Kit) and MCP (Model Context Protocol)**