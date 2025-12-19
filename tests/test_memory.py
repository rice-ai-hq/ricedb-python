import pytest
from unittest.mock import MagicMock
from ricedb.client.unified_client import RiceDBClient

def test_memory_client_interface():
    client = RiceDBClient(transport="http")
    # Mock the internal client
    client._client = MagicMock()
    
    # Test add
    client.memory.add("sess1", "agent1", "content")
    client._client.add_memory.assert_called_with("sess1", "agent1", "content", None)
    
    # Test get
    client.memory.get("sess1", limit=10)
    client._client.get_memory.assert_called_with("sess1", 10, None)
    
    # Test clear
    client.memory.clear("sess1")
    client._client.clear_memory.assert_called_with("sess1")
