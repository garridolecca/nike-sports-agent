import sys
from unittest.mock import MagicMock

# Mock dependencies that are not available in the environment
# This allows testing the logic of agent.py even if its dependencies are missing.
try:
    import dotenv
except ImportError:
    sys.modules["dotenv"] = MagicMock()

try:
    import cachetools
except ImportError:
    mock_cachetools = MagicMock()
    # Simple implementation of TTLCache for testing purposes
    class SimpleCache(dict):
        def __init__(self, maxsize=None, ttl=None):
            super().__init__()
    mock_cachetools.TTLCache = SimpleCache
    sys.modules["cachetools"] = mock_cachetools

try:
    import langchain_openai
except ImportError:
    sys.modules["langchain_openai"] = MagicMock()

try:
    import langchain_core
    import langchain_core.messages
except ImportError:
    sys.modules["langchain_core"] = MagicMock()
    sys.modules["langchain_core.messages"] = MagicMock()

try:
    import langgraph
    import langgraph.prebuilt
except ImportError:
    sys.modules["langgraph"] = MagicMock()
    sys.modules["langgraph.prebuilt"] = MagicMock()

try:
    import tools
except ImportError:
    sys.modules["tools"] = MagicMock()

# Now we can import the function to test
from agent import get_or_create_history, HISTORY_CACHE
import pytest

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the global history cache before each test."""
    HISTORY_CACHE.clear()

def test_get_or_create_history_creates_new_list():
    """Verify that a new session_id results in a new empty list in the cache."""
    session_id = "session-1"
    history = get_or_create_history(session_id)
    assert isinstance(history, list)
    assert len(history) == 0
    assert session_id in HISTORY_CACHE

def test_get_or_create_history_returns_existing_list():
    """Verify that an existing session_id returns the previously created list."""
    session_id = "session-1"
    history1 = get_or_create_history(session_id)
    history1.append("message 1")

    history2 = get_or_create_history(session_id)
    assert history2 is history1
    assert len(history2) == 1
    assert history2[0] == "message 1"

def test_get_or_create_history_independent_sessions():
    """Verify that different session_ids have independent history lists."""
    session_1 = "session-1"
    session_2 = "session-2"

    history1 = get_or_create_history(session_1)
    history2 = get_or_create_history(session_2)

    history1.append("msg from 1")
    assert "msg from 1" not in history2
    assert len(history2) == 0

def test_get_or_create_history_modifications_persist():
    """Verify that appending to the returned list persists it in the cache."""
    session_id = "session-1"
    history = get_or_create_history(session_id)
    history.append("persistent message")

    # Retrieve it again and check
    retrieved_history = get_or_create_history(session_id)
    assert "persistent message" in retrieved_history
    assert len(retrieved_history) == 1
