"""
Unit tests for ReportingAgent - Day 9

Tests the ReportingAgent functionality including report generation,
chart creation, and analytics engine integration.
"""

import base64
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from io import BytesIO

from apps.agents.decision.reporting_agent import ReportingAgent, AnalyticsEngine
from data.schemas import ReportRequest, ReportResult


class TestAnalyticsEngine:
    """Test cases for the AnalyticsEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analytics_engine = AnalyticsEngine()

    def test_init(self):
        """Test AnalyticsEngine initialization."""
        assert self.analytics_engine is not None
        # AnalyticsEngine uses module-level logger, not instance logger

    def test_analyze_anomaly_summary(self):
        """Test analyze method with anomaly_summary report type."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            time_range_start=datetime(2024, 1, 1),
            time_range_end=datetime(2024, 1, 31)
        )
        
        result = self.analytics_engine.analyze(request)
        
        # Check required fields are present
        assert "total_anomalies" in result
        assert "avg_anomalies_per_day" in result
        assert "chart_data" in result
        assert "sensors_affected" in result
        assert "false_positive_rate" in result
        
        # Check chart data structure
        chart_data = result["chart_data"]
        assert "dates" in chart_data
        assert "anomaly_counts" in chart_data
        assert chart_data["chart_type"] == "line"
        assert chart_data["title"] == "Anomalies Over Time"

    def test_analyze_maintenance_overview(self):
        """Test analyze method with maintenance_overview report type."""
        request = ReportRequest(
            report_type="maintenance_overview",
            format="json"
        )
        
        result = self.analytics_engine.analyze(request)
        
        # Check required fields
        assert "total_maintenance_tasks" in result
        assert "completed_tasks" in result
        assert "chart_data" in result
        
        # Check chart data for bar chart
        chart_data = result["chart_data"]
        assert chart_data["chart_type"] == "bar"
        assert "categories" in chart_data
        assert "values" in chart_data

    def test_analyze_system_health(self):
        """Test analyze method with system_health report type."""
        request = ReportRequest(
            report_type="system_health",
            format="json"
        )
        
        result = self.analytics_engine.analyze(request)
        
        # Check required fields
        assert "overall_system_health" in result
        assert "active_sensors" in result
        assert "chart_data" in result
        
        # Check chart data
        chart_data = result["chart_data"]
        assert chart_data["chart_type"] == "line"
        assert "uptime_percentages" in chart_data

    def test_analyze_unknown_report_type(self):
        """Test analyze method with unknown report type."""
        request = ReportRequest(
            report_type="unknown_type",
            format="json"
        )
        
        result = self.analytics_engine.analyze(request)
        
        assert result["report_type"] == "unknown"
        assert "data_points" in result
        assert "chart_data" in result
        assert result["chart_data"]["chart_type"] == "none"


class TestReportingAgent:
    """Test cases for the ReportingAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_event_bus = Mock()
        self.agent = ReportingAgent("test-reporting-agent", self.mock_event_bus)

    @pytest.mark.asyncio
    async def test_init(self):
        """Test ReportingAgent initialization."""
        assert self.agent.agent_id == "test-reporting-agent"
        assert self.agent.analytics_engine is not None
        assert isinstance(self.agent.analytics_engine, AnalyticsEngine)

    @pytest.mark.asyncio
    async def test_start(self):
        """Test agent start method."""
        await self.agent.start()
        assert self.agent.status == "running"

    @pytest.mark.asyncio
    async def test_stop(self):
        """Test agent stop method."""
        await self.agent.start()
        await self.agent.stop()
        assert self.agent.status == "stopped"

    @pytest.mark.asyncio
    async def test_get_health(self):
        """Test agent health status."""
        health = await self.agent.get_health()
        
        assert "analytics_engine_available" in health
        assert "supported_formats" in health
        assert "supported_report_types" in health
        assert health["analytics_engine_available"] is True
        assert "json" in health["supported_formats"]
        assert "text" in health["supported_formats"]

    @pytest.mark.asyncio
    async def test_register_capabilities(self):
        """Test agent capabilities registration."""
        capabilities = await self.agent.register_capabilities()
        
        expected_capabilities = [
            "report_generation",
            "data_visualization", 
            "kpi_calculation",
            "chart_creation"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method (placeholder)."""
        # Should not raise any exceptions
        await self.agent.process()

    def test_generate_report_json_format(self):
        """Test generate_report with JSON format."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            include_charts=True
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "total_anomalies": 42,
                "avg_anomalies_per_day": 1.4,
                "chart_data": {
                    "dates": ["2024-01-01", "2024-01-02"],
                    "anomaly_counts": [3, 5],
                    "chart_type": "line",
                    "title": "Test Chart"
                }
            }
            
            with patch.object(self.agent, '_generate_chart') as mock_chart:
                mock_chart.return_value = "base64encodedchart"
                
                result = self.agent.generate_report(request)
                
                assert isinstance(result, ReportResult)
                assert result.report_type == "anomaly_summary"
                assert result.format == "json"
                assert result.error_message is None
                
                # Check JSON content
                content_data = json.loads(result.content)
                assert content_data["total_anomalies"] == 42
                assert content_data["avg_anomalies_per_day"] == 1.4
                
                # Check charts
                assert "main_chart" in result.charts_encoded
                assert result.charts_encoded["main_chart"] == "base64encodedchart"
                
                # Verify analytics engine was called
                mock_analyze.assert_called_once_with(request)
                mock_chart.assert_called_once()

    def test_generate_report_text_format(self):
        """Test generate_report with text format."""
        request = ReportRequest(
            report_type="maintenance_overview",
            format="text",
            include_charts=False
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "total_maintenance_tasks": 25,
                "completed_tasks": 20,
                "pending_tasks": 3,
                "overdue_tasks": 2,
                "chart_data": None
            }
            
            result = self.agent.generate_report(request)
            
            assert result.format == "text"
            assert "MAINTENANCE OVERVIEW REPORT" in result.content
            assert "Total Tasks: 25" in result.content
            assert "Completion Rate:" in result.content
            assert len(result.charts_encoded) == 0  # No charts requested

    def test_generate_report_with_error(self):
        """Test generate_report when analytics engine raises an exception."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json"
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.side_effect = Exception("Analytics error")
            
            result = self.agent.generate_report(request)
            
            assert result.error_message == "Analytics error"
            assert result.content == ""
            assert len(result.charts_encoded) == 0

    def test_generate_report_without_charts(self):
        """Test generate_report when include_charts is False."""
        request = ReportRequest(
            report_type="system_health",
            format="json",
            include_charts=False
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "overall_system_health": 95.5,
                "chart_data": {"chart_type": "line", "title": "Test"}
            }
            
            result = self.agent.generate_report(request)
            
            assert len(result.charts_encoded) == 0

    def test_generate_json_content(self):
        """Test _generate_json_content method."""
        analytics_data = {
            "total_anomalies": 10,
            "avg_anomalies_per_day": 2.5,
            "chart_data": {"should": "be_removed"}
        }
        
        content = self.agent._generate_json_content(analytics_data)
        
        content_dict = json.loads(content)
        assert content_dict["total_anomalies"] == 10
        assert content_dict["avg_anomalies_per_day"] == 2.5
        assert "chart_data" not in content_dict

    def test_generate_text_content_anomaly_summary(self):
        """Test _generate_text_content for anomaly summary."""
        analytics_data = {
            "total_anomalies": 15,
            "avg_anomalies_per_day": 3.0,
            "anomaly_trend": "increasing",
            "sensors_affected": 8,
            "false_positive_rate": 0.12
        }
        
        content = self.agent._generate_text_content("anomaly_summary", analytics_data)
        
        assert "ANOMALY SUMMARY REPORT" in content
        assert "Total Anomalies: 15" in content
        assert "Average Anomalies per Day: 3.00" in content
        assert "Trend: Increasing" in content

    def test_generate_text_content_maintenance_overview(self):
        """Test _generate_text_content for maintenance overview."""
        analytics_data = {
            "total_maintenance_tasks": 30,
            "completed_tasks": 25,
            "pending_tasks": 3,
            "overdue_tasks": 2,
            "avg_completion_time": 4.5,
            "mttr_hours": 6.2
        }
        
        content = self.agent._generate_text_content("maintenance_overview", analytics_data)
        
        assert "MAINTENANCE OVERVIEW REPORT" in content
        assert "Total Tasks: 30" in content
        assert "Completed: 25" in content
        assert "Completion Rate: 83.3%" in content

    def test_generate_text_content_system_health(self):
        """Test _generate_text_content for system health."""
        analytics_data = {
            "overall_system_health": 96.5,
            "active_sensors": 45,
            "inactive_sensors": 3,
            "avg_response_time_ms": 125.5
        }
        
        content = self.agent._generate_text_content("system_health", analytics_data)
        
        assert "SYSTEM HEALTH REPORT" in content
        assert "Overall Health: 96.5%" in content
        assert "Active Sensors: 45" in content
        assert "Sensor Availability: 93.8%" in content

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.xticks')
    def test_generate_chart_line_chart(self, mock_xticks, mock_tight_layout, 
                                      mock_close, mock_savefig, mock_subplots):
        """Test _generate_chart for line chart generation."""
        # Setup mocks
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # Mock BytesIO
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake_image_data"
        
        with patch('io.BytesIO', return_value=mock_buffer):
            with patch('base64.b64encode') as mock_b64encode:
                mock_b64encode.return_value = b"encoded_chart_data"
                
                chart_data = {
                    "chart_type": "line",
                    "title": "Test Chart",
                    "xlabel": "X Label",
                    "ylabel": "Y Label",
                    "dates": ["2024-01-01", "2024-01-02"],
                    "anomaly_counts": [5, 8]
                }
                
                result = self.agent._generate_chart(chart_data)
                
                assert result == "encoded_chart_data"
                mock_subplots.assert_called_once_with(figsize=(10, 6))
                mock_ax.plot.assert_called_once()
                mock_ax.set_title.assert_called_once_with("Test Chart", fontsize=14, fontweight='bold')
                mock_savefig.assert_called_once()
                mock_close.assert_called_once()

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.tight_layout')
    def test_generate_chart_bar_chart(self, mock_tight_layout, mock_close, 
                                     mock_savefig, mock_subplots):
        """Test _generate_chart for bar chart generation."""
        # Setup mocks
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake_bar_chart_data"
        
        with patch('io.BytesIO', return_value=mock_buffer):
            with patch('base64.b64encode') as mock_b64encode:
                mock_b64encode.return_value = b"encoded_bar_chart"
                
                chart_data = {
                    "chart_type": "bar",
                    "title": "Bar Chart",
                    "categories": ["A", "B", "C"],
                    "values": [10, 15, 8]
                }
                
                result = self.agent._generate_chart(chart_data)
                
                assert result == "encoded_bar_chart"
                mock_ax.bar.assert_called_once_with(["A", "B", "C"], [10, 15, 8])

    def test_generate_chart_no_data(self):
        """Test _generate_chart with no chart data."""
        result = self.agent._generate_chart({})
        assert result is None
        
        result = self.agent._generate_chart({"chart_type": "none"})
        assert result is None

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.close')
    def test_generate_chart_exception_handling(self, mock_close, mock_subplots):
        """Test _generate_chart handles exceptions gracefully."""
        mock_subplots.side_effect = Exception("Matplotlib error")
        
        chart_data = {
            "chart_type": "line",
            "title": "Test Chart",
            "dates": ["2024-01-01"],
            "anomaly_counts": [5]
        }
        
        result = self.agent._generate_chart(chart_data)
        
        assert result is None
        mock_close.assert_called_once_with('all')

    def test_report_id_generation(self):
        """Test that report_id is generated when not provided."""
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json"
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {"total_anomalies": 5, "chart_data": None}
            
            result = self.agent.generate_report(request)
            
            assert result.report_id is not None
            assert result.report_id.startswith("report-")

    def test_report_id_preservation(self):
        """Test that provided report_id is preserved."""
        request = ReportRequest(
            report_id="custom-report-123",
            report_type="anomaly_summary",
            format="json"
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {"total_anomalies": 5, "chart_data": None}
            
            result = self.agent.generate_report(request)
            
            assert result.report_id == "custom-report-123"

    def test_metadata_population(self):
        """Test that report metadata is properly populated."""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 31)
        
        request = ReportRequest(
            report_type="anomaly_summary",
            format="json",
            time_range_start=start_time,
            time_range_end=end_time,
            parameters={"custom_param": "value"},
            include_charts=True
        )
        
        with patch.object(self.agent.analytics_engine, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                "total_anomalies": 5,
                "chart_data": {"dates": ["2024-01-01"], "anomaly_counts": [3]}
            }
            
            result = self.agent.generate_report(request)
            
            metadata = result.metadata
            assert metadata["parameters"] == {"custom_param": "value"}
            assert metadata["time_range_start"] == start_time.isoformat()
            assert metadata["time_range_end"] == end_time.isoformat()
            assert metadata["include_charts"] is True
            assert metadata["analytics_summary"]["data_points"] == 1
            assert metadata["analytics_summary"]["has_chart_data"] is True
