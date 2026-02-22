# Nike Sports Agent

An interactive geospatial application that combines ArcGIS maps with an AI-powered chat agent. Click on any map feature — Nike stores, sports events, or athletes — and ask the AI agent for deeper insights using natural language.

## Features

- **Interactive ArcGIS Map** — Four data layers rendered on a dark-themed map:
  - **Nike Stores** (purple) — Global retail store locations from ArcGIS Online
  - **Nike Events** (orange) — Sports events feature layer from ArcGIS Online
  - **Nike Athletes** (blue) — 40 Nike-sponsored athletes with home city coordinates (CSV)
  - **Sports Events** (red) — 2026 sports events with venue locations (CSV)
- **AI Chat Panel** — Side panel powered by Azure OpenAI (GPT-4.1) via LangGraph. Click any point on the map to auto-populate a question about that location.
- **Conversational Memory** — Per-session conversation history with TTL-based cache so the agent remembers context across turns.
- **Tool-Augmented Agent** — The LangGraph agent has six tools to query all four data sources, cross-reference them, and return structured answers.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend (index.html)                               │
│  ArcGIS JS API 4.33 + Calcite Components             │
│  Chat panel with Marked.js for markdown rendering     │
└────────────────────┬─────────────────────────────────┘
                     │  HTTP (fetch)
┌────────────────────▼─────────────────────────────────┐
│  FastAPI Backend (main.py)                            │
│  Endpoints: /chat, /athletes, /events-csv, /config    │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  LangGraph Agent (agent.py)                           │
│  Azure OpenAI (GPT-4.1) + 6 LangChain tools          │
└────────────────────┬─────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ArcGIS Online          Local CSV files
   (Feature Layers)       (athletes, events)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Map | ArcGIS JS API 4.33 (AMD), Calcite Components |
| Frontend | Vanilla HTML/CSS/JS, Marked.js |
| Backend | FastAPI, Uvicorn, ORJSON |
| AI Agent | LangGraph (`create_react_agent`), LangChain |
| LLM | Azure OpenAI (GPT-4.1) |
| Data | ArcGIS Online Feature Layers, Pandas (CSV) |
| GIS SDK | ArcGIS Python API (`arcgis`) |

## Prerequisites

- **Python 3.12** (the `arcgis` package is not yet compatible with Python 3.13+)
- **Azure OpenAI** API key and endpoint
- **ArcGIS Online** API key (for basemap and feature layer access)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/garridolecca/nike-sports-agent.git
   cd nike-sports-agent
   ```

2. **Create a virtual environment with Python 3.12**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate        # Linux/macOS
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your keys:
   ```
   OPENAI_API_KEY=your-azure-openai-api-key
   AZURE_API_BASE=https://your-endpoint.azure-api.net/...
   AZURE_API_DEPLOYMENT=gpt-4.1
   AZURE_API_VERSION=2024-10-21
   ARCGIS_API_KEY=your-arcgis-api-key
   ```

5. **Run the server**
   ```bash
   python main.py
   ```
   Open [http://localhost:8000](http://localhost:8000) in your browser.

## Data Sources

| Source | Type | Description |
|--------|------|------------|
| Nike Stores | ArcGIS Online FeatureServer/1 | Global Nike retail locations with fields like FACILITY_NAME, CITY, COUNTRY |
| Nike Events | ArcGIS Online FeatureServer/10 | Sports events layer with fields like title, locality, venue_name |
| Athletes CSV | Local CSV | 40 Nike-sponsored athletes — name, sport, country, home coordinates, team, specialty |
| Events CSV | Local CSV | 2026 sports events — event name, sport, dates, venue coordinates, region |

## Agent Tools

The AI agent has access to six tools:

| Tool | Data Source | Purpose |
|------|-----------|---------|
| `describe_nike_stores` | ArcGIS Online | Get schema/metadata of the Nike Stores layer |
| `query_nike_stores` | ArcGIS Online | Query stores with SQL WHERE clauses |
| `describe_events_layer` | ArcGIS Online | Get schema/metadata of the Events layer |
| `query_events_layer` | ArcGIS Online | Query events with SQL WHERE clauses |
| `query_athletes` | CSV | Search athletes by sport or country |
| `query_events_csv` | CSV | Search 2026 events by sport or region |

## API Endpoints

| Method | Path | Description |
|--------|------|------------|
| GET | `/` | Serve the frontend |
| POST | `/chat` | Send a message to the AI agent |
| GET | `/athletes` | Get all athletes as JSON |
| GET | `/events-csv` | Get all events as JSON |
| GET | `/config` | Get frontend config (ArcGIS API key) |
| POST | `/reset` | Clear a session's conversation history |
| GET | `/health` | Health check |

## License

This project is for demonstration and educational purposes.
