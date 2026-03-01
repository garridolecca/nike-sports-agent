import sys
from unittest.mock import MagicMock, patch
import pandas as pd

# Mock missing modules
sys.modules['arcgis'] = MagicMock()
sys.modules['arcgis.gis'] = MagicMock()
sys.modules['arcgis.features'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.tools'] = MagicMock()

# Import the module to test
from tools import _load_athletes, _load_athletes_cached, _load_events, _load_events_cached

def test_cache_and_copy_athletes():
    # Clear the cache to ensure clean state
    _load_athletes_cached.cache_clear()

    # Create dummy data
    dummy_data = pd.DataFrame([{"name": "Athlete 1"}, {"name": "Athlete 2"}])

    with patch('pandas.read_csv', return_value=dummy_data) as mock_read_csv:
        # First call should trigger read_csv
        df1 = _load_athletes()
        mock_read_csv.assert_called_once()
        assert df1.equals(dummy_data)

        # Modifying df1 should not affect the cache
        df1.loc[0, "name"] = "Modified"

        # Second call should not trigger read_csv
        df2 = _load_athletes()
        assert mock_read_csv.call_count == 1
        assert df2.loc[0, "name"] == "Athlete 1"  # Remains unchanged from original

def test_cache_and_copy_events():
    # Clear the cache to ensure clean state
    _load_events_cached.cache_clear()

    # Create dummy data
    dummy_data = pd.DataFrame([{"event_name": "Event 1"}, {"event_name": "Event 2"}])

    with patch('pandas.read_csv', return_value=dummy_data) as mock_read_csv:
        # First call should trigger read_csv
        df1 = _load_events()
        mock_read_csv.assert_called_once()
        assert df1.equals(dummy_data)

        # Modifying df1 should not affect the cache
        df1.loc[0, "event_name"] = "Modified"

        # Second call should not trigger read_csv
        df2 = _load_events()
        assert mock_read_csv.call_count == 1
        assert df2.loc[0, "event_name"] == "Event 1"  # Remains unchanged from original
