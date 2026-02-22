"""
LangGraph agent with Azure OpenAI and per-session conversation history.
"""

import os
from dotenv import load_dotenv
from cachetools import TTLCache

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from tools import (
    describe_nike_stores,
    query_nike_stores,
    describe_events_layer,
    query_events_layer,
    query_athletes,
    query_events_csv,
)

load_dotenv()

# =============================================================================
# LLM
# =============================================================================

_llm = AzureChatOpenAI(
    azure_endpoint=os.environ.get("AZURE_API_BASE"),
    azure_deployment=os.environ.get("AZURE_API_DEPLOYMENT", "gpt-4.1"),
    api_version=os.environ.get("AZURE_API_VERSION", "2024-10-21"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0,
    streaming=False,
)

# =============================================================================
# TOOLS
# =============================================================================

_TOOLS = [
    describe_nike_stores,
    query_nike_stores,
    describe_events_layer,
    query_events_layer,
    query_athletes,
    query_events_csv,
]

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

_SYSTEM_PROMPT = """You are a Nike Sports geospatial analyst with access to four data sources:

1. **Nike Stores (ArcGIS Online)** — Global Nike retail store locations.
   Tools: describe_nike_stores, query_nike_stores

2. **Nike Events (ArcGIS Online)** — Sports events feature layer from AGOL.
   Tools: describe_events_layer, query_events_layer

3. **Nike Athletes (CSV)** — 40 Nike-sponsored athletes with home city coordinates.
   Tool: query_athletes  |  Fields: name, sport, country, home_city, home_lat, home_lon, team_club, specialty, nike_category

4. **Sports Events (CSV)** — 2026 sports events with venue coordinates.
   Tool: query_events_csv  |  Fields: event_name, sport, start_date, end_date, city, country, venue, lat, lon, region

When answering questions:
- Always use the correct tool for the data source being asked about.
- For schema questions, call describe_* tools first, then query.
- Cross-reference data sources when relevant (e.g. athletes near event locations).
- Present results as a clear markdown table when returning multiple records.
- Never fabricate data — if a query returns nothing, say so and suggest alternatives.
- Format numbers with commas. Use concise, professional language.
"""

# =============================================================================
# AGENT (LangGraph react agent)
# =============================================================================

_agent = create_react_agent(
    model=_llm,
    tools=_TOOLS,
    prompt=_SYSTEM_PROMPT,
)

# =============================================================================
# SESSION HISTORY (TTLCache)
# =============================================================================

HISTORY_CACHE: TTLCache = TTLCache(maxsize=500, ttl=3600)


def get_or_create_history(session_id: str) -> list:
    if session_id not in HISTORY_CACHE:
        HISTORY_CACHE[session_id] = []
    return HISTORY_CACHE[session_id]


def run_agent(session_id: str, user_message: str) -> str:
    """Run the agent for a session and return the text reply."""
    history = get_or_create_history(session_id)

    messages = list(history) + [HumanMessage(content=user_message)]

    result = _agent.invoke({"messages": messages})

    # Extract the last AI message from the result
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage) and m.content]
    reply = ai_messages[-1].content if ai_messages else "I was unable to generate a response."

    # Append to rolling history and refresh TTL
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=reply))
    HISTORY_CACHE[session_id] = history

    return reply


def clear_session(session_id: str) -> None:
    """Clear conversation history for a session."""
    HISTORY_CACHE.pop(session_id, None)
