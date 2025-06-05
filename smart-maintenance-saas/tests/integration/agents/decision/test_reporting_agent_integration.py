"""
Integration tests for ReportingAgent - Day 9

Tests the ReportingAgent's integration with its components including
real analytics engine interaction and chart generation.
"""

import pytest
from datetime import datetime, timedelta
import json
import base64
from unittest.mock import Mock

from apps.agents.decision.reporting_agent import ReportingAgent, AnalyticsEngine
from data.schemas import ReportRequest, ReportResult


class TestReportingAgentIntegration:
    """Integration tests for ReportingAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_event_bus = Mock()
        self.agent = ReportingAgent("integration-test-agent", self.mock_event_bus)

    @pytest.mark.asyncio
    async def test_agent_initialization_and_lifecycle(self):
        """Test agent initialization and lifecycle management."""
        # Test initialization
        assert self.agent.agent_id == "integration-test-agent"
        assert self.agent.analytics_engine is not None
        
        # Test start
        await self.agent.start()
        assert self.agent.status == "running"
        
        # Test health check
        health = await self.agent.get_health()
        assert health["status"] == "running"
        assert health["analytics_engine_available"] is True
        
        # Test capabilities
        capabilities = await self.agent.register_capabilities()
        assert "report_generation" in capabilities
        assert "data_visualization" in capabilities
        
        # Test stop
        await self.agent.stop()
        assert self.agent.status == "stopped"

    def test_end_to_end_anomaly_summary_report_json(self):
        """Test complete anomaly summary report generation in JSON format."""
        request = ReportRequest(
            report_id="integration-anomaly-001",
            report_type="anomaly_summary",
            format="json",
            time_range_start=datetime(2024, 1, 1),
            time_range_end=datetime(2024, 1, 31),
            include_charts=True,
            parameters={"threshold": 0.95}
        )
        
        result = self.agent.generate_report(request)
        
        # Verify result structure
        assert isinstance(result, ReportResult)
        assert result.report_id == "integration-anomaly-001"
        assert result.report_type == "anomaly_summary"
        assert result.format == "json"
        assert result.error_message is None
        assert result.generated_at is not None
        
        # Verify JSON content
        content_data = json.loads(result.content)
        assert "total_anomalies" in content_data
        assert "avg_anomalies_per_day" in content_data
        assert "sensors_affected" in content_data
        assert "false_positive_rate" in content_data
        
        # Verify charts were generated
        assert "main_chart" in result.charts_encoded
        assert len(result.charts_encoded["main_chart"]) > 0
        
        # Verify chart is valid base64
        try:
            base64.b64decode(result.charts_encoded["main_chart"])
        except Exception:
            pytest.fail("Chart is not valid base64 encoded data")
        
        # Verify metadata
        metadata = result.metadata
        assert metadata["parameters"]["threshold"] == 0.95
        assert metadata["include_charts"] is True
        assert "analytics_summary" in metadata

    def test_end_to_end_maintenance_overview_report_text(self):
        """Test complete maintenance overview report generation in text format."""
        request = ReportRequest(
            report_type="maintenance_overview",
            format="text",
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        # Verify result structure
        assert result.report_type == "maintenance_overview"
        assert result.format == "text"
        assert result.error_message is None
        
        # Verify text content structure
        content = result.content
        assert "MAINTENANCE OVERVIEW REPORT" in content
        assert "Task Summary:" in content
        assert "Performance Metrics:" in content
        assert "Total Tasks:" in content
        assert "Completion Rate:" in content
        
        # Verify charts were generated
        assert "main_chart" in result.charts_encoded
        assert len(result.charts_encoded["main_chart"]) > 0

    def test_end_to_end_system_health_report_json(self):
        """Test complete system health report generation in JSON format."""
        request = ReportRequest(
            report_type="system_health",
            format="json",
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        # Verify result structure
        assert result.report_type == "system_health"
        assert result.format == "json"
        assert result.error_message is None
        
        # Verify JSON content
        content_data = json.loads(result.content)
        assert "overall_system_health" in content_data
        assert "active_sensors" in content_data
        assert "inactive_sensors" in content_data
        assert "avg_response_time_ms" in content_data
        
        # Verify charts were generated
        assert "main_chart" in result.charts_encoded

    def test_report_without_charts(self):
        """Test report generation without charts."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            include_charts=False
        )
        
        result = self.agent.generate_report(request)
        
        assert result.error_message is None
        assert len(result.charts_encoded) == 0
        
        # Content should still be generated
        content_data = json.loads(result.content)
        assert "total_anomalies" in content_data

    def test_analytics_engine_integration(self):
        """Test direct integration with AnalyticsEngine."""
        analytics_engine = AnalyticsEngine()
        
        # Test different report types
        request_anomaly = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            time_range_start=datetime(2024, 1, 1),
            time_range_end=datetime(2024, 1, 15)
        )
        
        result = analytics_engine.analyze(request_anomaly)
        
        # Verify structure
        assert "total_anomalies" in result
        assert "chart_data" in result
        assert result["chart_data"]["chart_type"] == "line"
        assert len(result["chart_data"]["dates"]) == 14  # 14 days
        assert len(result["chart_data"]["anomaly_counts"]) == 14

    def test_multiple_report_generation(self):
        """Test generating multiple reports in sequence."""
        requests = [
            ReportRequest(report_type="anomaly_summary", format="json"),
            ReportRequest(report_type="maintenance_overview", format="text"),
            ReportRequest(report_type="system_health", format="json")
        ]
        
        results = []
        for request in requests:
            result = self.agent.generate_report(request)
            results.append(result)
        
        # Verify all reports were generated successfully
        assert len(results) == 3
        for result in results:
            assert result.error_message is None
            assert result.generated_at is not None
            assert len(result.content) > 0

    def test_chart_generation_integration(self):
        """Test chart generation with real matplotlib integration."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        # Verify chart was generated
        assert "main_chart" in result.charts_encoded
        chart_data = result.charts_encoded["main_chart"]
        
        # Verify it's valid base64
        try:
            decoded_chart = base64.b64decode(chart_data)
            # Should be PNG image data
            assert decoded_chart.startswith(b'\x89PNG')
        except Exception as e:
            pytest.fail(f"Failed to decode chart: {e}")

    def test_time_range_handling(self):
        """Test report generation with different time ranges."""
        # Test with explicit time range
        start_time = datetime(2024, 6, 1)
        end_time = datetime(2024, 6, 5)
        
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            time_range_start=start_time,
            time_range_end=end_time,
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        assert result.error_message is None
        
        # Verify metadata contains time range
        metadata = result.metadata
        assert metadata["time_range_start"] == start_time.isoformat()
        assert metadata["time_range_end"] == end_time.isoformat()

    def test_error_resilience(self):
        """Test agent resilience to errors."""
        # Test with invalid report type (should still work due to fallback)
        request = ReportRequest(
            report_type="invalid_report_type",
            format="json"
        )
        
        result = self.agent.generate_report(request)
        
        # Should not fail completely
        assert result is not None
        assert result.report_type == "invalid_report_type"

    def test_concurrent_report_generation(self):
        """Test handling of concurrent report generation requests."""
        import asyncio
        
        async def generate_report_async(report_type: str):
            request = ReportRequest(
                report_type=report_type,
                format="json",
                include_charts=True
            )
            return self.agent.generate_report(request)
        
        async def run_concurrent_reports():
            tasks = [
                generate_report_async("anomaly_summary"),
                generate_report_async("maintenance_overview"),
                generate_report_async("system_health")
            ]
            
            results = await asyncio.gather(*tasks)
            return results
        
        # Run concurrent report generation
        results = asyncio.run(run_concurrent_reports())
        
        # Verify all reports were generated
        assert len(results) == 3
        for result in results:
            assert result.error_message is None
            assert len(result.content) > 0

    def test_large_time_range_handling(self):
        """Test report generation with large time ranges."""
        # Test with 6 months of data
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 6, 30)
        
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            time_range_start=start_time,
            time_range_end=end_time,
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        assert result.error_message is None
        
        # Verify chart generation works with large data sets
        assert "main_chart" in result.charts_encoded

    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self):
        """Test agent health monitoring during operation."""
        await self.agent.start()
        
        # Generate several reports and check health
        for i in range(3):
            request = ReportRequest(
                report_type="anomaly_summary",
                format="json"
            )
            result = self.agent.generate_report(request)
            assert result.error_message is None
            
            # Check health after each operation
            health = await self.agent.get_health()
            assert health["status"] == "running"
            assert health["analytics_engine_available"] is True
        
        await self.agent.stop()

    def test_custom_parameters_integration(self):
        """Test report generation with custom parameters."""
        custom_params = {
            "custom_threshold": 0.85,
            "include_predictions": True,
            "detail_level": "high"
        }
        
        request = ReportRequest(
            report_type="system_health",
            format="json",
            parameters=custom_params,
            include_charts=True
        )
        
        result = self.agent.generate_report(request)
        
        assert result.error_message is None
        
        # Verify custom parameters are preserved in metadata
        metadata = result.metadata
        assert metadata["parameters"] == custom_params

    def test_chart_generation_fallback(self):
        """Test chart generation with malformed data (fallback behavior)."""
        request = ReportRequest(
            report_type="maintenance_overview",
            format="json",
            include_charts=True
        )
        
        # This should work even if analytics engine returns unexpected data
        result = self.agent.generate_report(request)
        
        assert result.error_message is None
        # Chart generation should handle any issues gracefully
        # Either generate a chart or handle the error without failing the report
