"""
LangChain tools for Nike Sports Agent.
Wraps ArcGIS Online feature layer queries and local CSV data.
"""

import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_core.tools import tool
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

load_dotenv()

# =============================================================================
# CONSTANTS
# =============================================================================

NIKE_STORES_URL = (
    "https://services2.arcgis.com/cPVqgcKAQtE6xCja/arcgis/rest/services/"
    "Nike_Story/FeatureServer/1"
)
EVENTS_AGOL_URL = (
    "https://services2.arcgis.com/cPVqgcKAQtE6xCja/arcgis/rest/services/"
    "Nike_Story/FeatureServer/10"
)

# CSV paths relative to this file's parent directory
_BASE = Path(__file__).parent
ATHLETES_CSV = Path(os.environ.get("ATHLETES_CSV_PATH", _BASE / "data/athletes.csv"))
EVENTS_CSV   = Path(os.environ.get("EVENTS_CSV_PATH", _BASE / "data/events.csv"))


# =============================================================================
# ArcGIS connection (pattern from Nike_sample/functions/core_spatial.py:23)
# =============================================================================

def _get_gis() -> GIS:
    """Return a GIS connection using the API key, or anonymous if not set."""
    api_key = os.environ.get("ARCGIS_API_KEY", "")
    if api_key:
        return GIS("https://www.arcgis.com/", api_key=api_key)
    return GIS()  # anonymous — works for public layers


# =============================================================================
# AGOL TOOLS
# =============================================================================

@tool
def describe_nike_stores() -> str:
    """
    Get the schema and metadata of the Nike Stores ArcGIS feature layer.
    Returns field names, types, geometry type, and description.
    Call this before querying Nike stores to understand what fields are available.
    """
    try:
        gis = _get_gis()
        fl = FeatureLayer(NIKE_STORES_URL, gis=gis)
        props = fl.properties
        fields = [
            {"name": f["name"], "type": f["type"], "alias": f.get("alias", f["name"])}
            for f in props.get("fields", [])
        ]
        return json.dumps({
            "layer": "Nike Stores",
            "name": props.get("name", "Unknown"),
            "description": props.get("description", ""),
            "geometry_type": props.get("geometryType", "Unknown"),
            "object_id_field": props.get("objectIdField", "OBJECTID"),
            "fields": fields,
            "max_record_count": props.get("maxRecordCount", 1000),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def query_nike_stores(
    where_clause: str = "1=1",
    fields: str = "*",
    max_records: int = 20,
) -> str:
    """
    Query the Nike Stores ArcGIS Online feature layer using a SQL WHERE clause.
    Use describe_nike_stores() first to see available fields.

    Args:
        where_clause: SQL WHERE expression, e.g. "COUNTRY = 'US'" or "1=1" for all.
        fields: Comma-separated field names to return, or "*" for all fields.
        max_records: Maximum number of records to return (default 20, max 100).
    """
    try:
        gis = _get_gis()
        fl = FeatureLayer(NIKE_STORES_URL, gis=gis)
        max_records = min(max_records, 100)
        fset = fl.query(
            where=where_clause,
            out_fields=fields,
            return_geometry=False,
            result_record_count=max_records,
        )
        if not fset.features:
            return json.dumps({"count": 0, "features": [], "message": "No stores matched the query."})
        records = [f.attributes for f in fset.features]
        return json.dumps({"count": len(records), "layer": "Nike Stores", "features": records},
                          indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "hint": "Check where_clause syntax."})


@tool
def describe_events_layer() -> str:
    """
    Get the schema and metadata of the Nike Events ArcGIS feature layer.
    Returns field names, types, geometry type, and description.
    Call this before querying the events layer to understand what fields are available.
    """
    try:
        gis = _get_gis()
        fl = FeatureLayer(EVENTS_AGOL_URL, gis=gis)
        props = fl.properties
        fields = [
            {"name": f["name"], "type": f["type"], "alias": f.get("alias", f["name"])}
            for f in props.get("fields", [])
        ]
        return json.dumps({
            "layer": "Nike Events (AGOL)",
            "name": props.get("name", "Unknown"),
            "description": props.get("description", ""),
            "geometry_type": props.get("geometryType", "Unknown"),
            "object_id_field": props.get("objectIdField", "OBJECTID"),
            "fields": fields,
            "max_record_count": props.get("maxRecordCount", 1000),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def query_events_layer(
    where_clause: str = "1=1",
    fields: str = "*",
    max_records: int = 20,
) -> str:
    """
    Query the Nike Events ArcGIS Online feature layer using a SQL WHERE clause.
    Use describe_events_layer() first to see available fields.

    Args:
        where_clause: SQL WHERE expression, e.g. "SPORT = 'Soccer'" or "1=1" for all.
        fields: Comma-separated field names to return, or "*" for all fields.
        max_records: Maximum number of records to return (default 20, max 100).
    """
    try:
        gis = _get_gis()
        fl = FeatureLayer(EVENTS_AGOL_URL, gis=gis)
        max_records = min(max_records, 100)
        fset = fl.query(
            where=where_clause,
            out_fields=fields,
            return_geometry=False,
            result_record_count=max_records,
        )
        if not fset.features:
            return json.dumps({"count": 0, "features": [], "message": "No events matched the query."})
        records = [f.attributes for f in fset.features]
        return json.dumps({"count": len(records), "layer": "Nike Events (AGOL)", "features": records},
                          indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "hint": "Check where_clause syntax."})


# =============================================================================
# CSV TOOLS
# =============================================================================

def _load_athletes() -> pd.DataFrame:
    return pd.read_csv(ATHLETES_CSV)


def _load_events() -> pd.DataFrame:
    return pd.read_csv(EVENTS_CSV)


@tool
def query_athletes(
    filter_sport: str = "",
    filter_country: str = "",
    max_results: int = 20,
) -> str:
    """
    Search the Nike Athletes CSV dataset. Returns athlete name, sport, country,
    home city, coordinates (home_lat, home_lon), team/club, and specialty.

    Args:
        filter_sport: Filter by sport name (e.g. "Soccer", "Basketball"). Empty = all sports.
        filter_country: Filter by country name (e.g. "USA", "France"). Empty = all countries.
        max_results: Maximum athletes to return (default 20).
    """
    try:
        df = _load_athletes()
        if filter_sport:
            df = df[df["sport"].str.lower().str.contains(filter_sport.lower(), na=False)]
        if filter_country:
            df = df[df["country"].str.lower().str.contains(filter_country.lower(), na=False)]
        df = df.head(max_results)
        if df.empty:
            return json.dumps({"count": 0, "athletes": [], "message": "No athletes matched the filters."})
        records = df.to_dict(orient="records")
        return json.dumps({"count": len(records), "source": "athletes.csv", "athletes": records},
                          indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def query_events_csv(
    filter_sport: str = "",
    filter_region: str = "",
    max_results: int = 20,
) -> str:
    """
    Search the Nike Sports Events CSV dataset. Returns event name, sport, dates,
    city, country, venue, coordinates (lat, lon), and region.

    Args:
        filter_sport: Filter by sport name (e.g. "Soccer", "Multi-Sport"). Empty = all sports.
        filter_region: Filter by region (e.g. "Europe", "North America"). Empty = all regions.
        max_results: Maximum events to return (default 20).
    """
    try:
        df = _load_events()
        if filter_sport:
            df = df[df["sport"].str.lower().str.contains(filter_sport.lower(), na=False)]
        if filter_region:
            df = df[df["region"].str.lower().str.contains(filter_region.lower(), na=False)]
        df = df.head(max_results)
        if df.empty:
            return json.dumps({"count": 0, "events": [], "message": "No events matched the filters."})
        records = df.to_dict(orient="records")
        return json.dumps({"count": len(records), "source": "events.csv", "events": records},
                          indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# CSV DATA LOADERS (for FastAPI endpoints — not LangChain tools)
# =============================================================================

def load_athletes_json() -> list[dict]:
    """Load athletes CSV and return as list of dicts (for /athletes endpoint)."""
    df = _load_athletes()
    return df.to_dict(orient="records")


def load_events_json() -> list[dict]:
    """Load events CSV and return as list of dicts (for /events-csv endpoint)."""
    df = _load_events()
    return df.to_dict(orient="records")
