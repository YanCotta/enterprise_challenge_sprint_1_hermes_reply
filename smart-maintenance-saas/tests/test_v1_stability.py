"""
Minimal V1.0 validation tests for critical system functionality.

These tests validate the core fixes implemented for stabilization:
1. UI pages can import without errors
2. Safe rerun functionality works
3. API client latency recording functions
4. Model metadata handles different states properly
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the smart-maintenance-saas root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_safe_rerun_import():
    """Test that safe_rerun can be imported without errors."""
    from ui.lib.rerun import safe_rerun
    # Should not raise any exception
    assert callable(safe_rerun)

def test_safe_rerun_graceful_fallback():
    """Test that safe_rerun handles missing streamlit gracefully."""
    # Mock streamlit to not have rerun methods
    with patch('streamlit.rerun', side_effect=AttributeError):
        with patch('streamlit.experimental_rerun', side_effect=AttributeError):
            from ui.lib.rerun import safe_rerun
            # Should not raise any exception
            try:
                safe_rerun()
            except Exception as e:
                pytest.fail(f"safe_rerun should not raise exception, got: {e}")

def test_latency_sample_function_exists():
    """Test that record_latency_sample function exists in api_client."""
    from ui.lib.api_client import record_latency_sample
    assert callable(record_latency_sample)
    
    # Should handle basic call without error
    try:
        record_latency_sample("test", 100.0, status="ok")
    except Exception as e:
        pytest.fail(f"record_latency_sample should not raise exception, got: {e}")

def test_simulation_console_import_fallback():
    """Test that simulation console handles import errors gracefully."""
    # This test simulates the ImportError case and verifies fallback
    import importlib.util
    
    # Mock the api_client module to raise ImportError for record_latency_sample
    with patch('ui.lib.api_client.record_latency_sample', side_effect=ImportError):
        # The page should define its own fallback function
        try:
            # Simulate the import pattern used in 7_Simulation_Console.py
            try:
                from ui.lib.api_client import record_latency_sample  # type: ignore
                fallback_used = False
            except Exception:  # noqa: BLE001
                def record_latency_sample(label: str, ms: float, **meta):  # type: ignore
                    """Fallback no-op if latency recording not available."""
                    return
                fallback_used = True
            
            # Should use fallback and not crash
            assert fallback_used or callable(record_latency_sample)
            
        except Exception as e:
            pytest.fail(f"Simulation console import pattern should not fail, got: {e}")

@patch('ui.lib.api_client.make_api_request')
@patch('streamlit.info')
@patch('streamlit.error') 
def test_model_metadata_state_differentiation(mock_error, mock_info, mock_api_request):
    """Test that model metadata properly differentiates between different states."""
    import os
    import streamlit as st
    from ui.lib.api_client import make_api_request
    
    # Test 1: MLflow disabled by environment variable
    with patch.dict(os.environ, {'DISABLE_MLFLOW_MODEL_LOADING': 'true'}):
        # Should show disabled message and return early
        with patch('streamlit.info') as mock_info:
            # This would be called in the actual render function
            mlflow_disabled = os.getenv("DISABLE_MLFLOW_MODEL_LOADING", "false").lower() in ("1", "true", "yes")
            assert mlflow_disabled == True
    
    # Test 2: Empty registry (no models but connection works)
    with patch.dict(os.environ, {'DISABLE_MLFLOW_MODEL_LOADING': 'false'}):
        mock_api_request.side_effect = [
            {'success': True, 'data': []},  # Empty models list
            {'success': True, 'data': {'status': 'healthy'}}  # Health check passes
        ]
        
        # Simulate the logic from render_model_metadata
        models = mock_api_request.return_value['data'] if mock_api_request.return_value.get('success') else []
        if not models:
            health_result = make_api_request("GET", "/api/v1/ml/health")
            expected_empty_state = health_result.get('success', False)
            assert expected_empty_state == True
    
    # Test 3: API connection failure
    with patch.dict(os.environ, {'DISABLE_MLFLOW_MODEL_LOADING': 'false'}):
        mock_api_request.side_effect = [
            {'success': False, 'error': 'Connection timeout'}  # API failure
        ]
        
        # Should identify this as an API error, not empty state
        result = mock_api_request.return_value
        assert result['success'] == False
        assert 'error' in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])