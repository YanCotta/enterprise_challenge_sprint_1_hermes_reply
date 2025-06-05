"""
ReportingAgent - Day 9 Implementation

This module implements the ReportingAgent for generating simple text/JSON reports 
with basic analytics and matplotlib charts for the Smart Maintenance SaaS system.
"""

import base64
import io
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import random

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from apps.agents.base_agent import BaseAgent
from data.schemas import ReportRequest, ReportResult
from core.logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


class AnalyticsEngine:
    """
    Mock analytics engine that simulates database fetching and KPI calculation.
    In a real implementation, this would connect to actual databases and perform
    complex analytics queries.
    """

    def __init__(self):
        pass

    def analyze(self, report_request: ReportRequest) -> Dict[str, Any]:
        """
        Analyze data and return KPIs and chart data.
        
        Args:
            report_request: The report request containing parameters
            
        Returns:
            Dictionary containing analytics results including chart_data
        """
        logger.info(f"Analyzing data for report type: {report_request.report_type}")
        
        # Mock time range
        end_time = report_request.time_range_end or datetime.utcnow()
        start_time = report_request.time_range_start or (end_time - timedelta(days=30))
        
        # Generate mock data based on report type
        if report_request.report_type == "anomaly_summary":
            return self._generate_anomaly_summary_data(start_time, end_time)
        elif report_request.report_type == "maintenance_overview":
            return self._generate_maintenance_overview_data(start_time, end_time)
        elif report_request.report_type == "system_health":
            return self._generate_system_health_data(start_time, end_time)
        else:
            return self._generate_default_data(start_time, end_time)

    def _generate_anomaly_summary_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate mock anomaly summary data."""
        days = (end_time - start_time).days
        
        # Generate time series data
        dates = [start_time + timedelta(days=i) for i in range(days)]
        anomaly_counts = [random.randint(0, 10) for _ in range(days)]
        
        return {
            "total_anomalies": sum(anomaly_counts),
            "avg_anomalies_per_day": sum(anomaly_counts) / len(anomaly_counts) if anomaly_counts else 0,
            "peak_anomaly_day": max(anomaly_counts) if anomaly_counts else 0,
            "anomaly_trend": "increasing" if random.choice([True, False]) else "stable",
            "chart_data": {
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "anomaly_counts": anomaly_counts,
                "chart_type": "line",
                "title": "Anomalies Over Time",
                "xlabel": "Date",
                "ylabel": "Anomaly Count"
            },
            "sensors_affected": random.randint(5, 20),
            "false_positive_rate": round(random.uniform(0.05, 0.15), 3)
        }

    def _generate_maintenance_overview_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate mock maintenance overview data."""
        return {
            "total_maintenance_tasks": random.randint(20, 50),
            "completed_tasks": random.randint(15, 40),
            "pending_tasks": random.randint(2, 8),
            "overdue_tasks": random.randint(0, 3),
            "avg_completion_time": round(random.uniform(2.5, 8.0), 2),
            "mttr_hours": round(random.uniform(4.0, 12.0), 2),
            "chart_data": {
                "categories": ["Completed", "Pending", "Overdue"],
                "values": [random.randint(15, 40), random.randint(2, 8), random.randint(0, 3)],
                "chart_type": "bar",
                "title": "Maintenance Task Status",
                "xlabel": "Task Status",
                "ylabel": "Number of Tasks"
            },
            "technician_utilization": round(random.uniform(0.70, 0.95), 3),
            "equipment_uptime": round(random.uniform(0.92, 0.99), 3)
        }

    def _generate_system_health_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate mock system health data."""
        days = min((end_time - start_time).days, 14)  # Last 14 days max
        dates = [start_time + timedelta(days=i) for i in range(days)]
        uptime_percentages = [round(random.uniform(95.0, 99.9), 2) for _ in range(days)]
        
        return {
            "overall_system_health": round(random.uniform(85.0, 98.0), 2),
            "active_sensors": random.randint(50, 150),
            "inactive_sensors": random.randint(2, 10),
            "avg_response_time_ms": round(random.uniform(50.0, 200.0), 2),
            "data_quality_score": round(random.uniform(0.85, 0.98), 3),
            "chart_data": {
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "uptime_percentages": uptime_percentages,
                "chart_type": "line",
                "title": "System Uptime Over Time",
                "xlabel": "Date",
                "ylabel": "Uptime (%)"
            },
            "alerts_generated": random.randint(10, 50),
            "critical_alerts": random.randint(0, 5)
        }

    def _generate_default_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate default mock data for unknown report types."""
        return {
            "report_type": "unknown",
            "data_points": random.randint(100, 1000),
            "processing_time_ms": round(random.uniform(10.0, 100.0), 2),
            "chart_data": {
                "dates": [],
                "values": [],
                "chart_type": "none",
                "title": "No Data Available",
                "xlabel": "",
                "ylabel": ""
            }
        }


class ReportingAgent(BaseAgent):
    """
    ReportingAgent generates reports with KPIs and visualizations from system data.
    
    This agent can generate various types of reports including:
    - Anomaly summaries with trend analysis
    - Maintenance overviews with task statistics
    - System health reports with uptime metrics
    
    Reports can be generated in JSON or text format and include matplotlib charts
    encoded as base64 strings.
    """

    def __init__(self, agent_id: str = None, event_bus=None):
        """
        Initialize the ReportingAgent.
        
        Args:
            agent_id: Optional agent identifier. If not provided, a UUID will be generated.
            event_bus: Event bus instance for inter-agent communication.
        """
        super().__init__(agent_id or f"reporting-agent-{uuid.uuid4().hex[:8]}", event_bus)
        self.analytics_engine = AnalyticsEngine()
        logger.info(f"ReportingAgent {self.agent_id} initialized")

    async def start(self) -> None:
        """Start the ReportingAgent."""
        await super().start()
        logger.info(f"ReportingAgent {self.agent_id} started successfully")

    async def stop(self) -> None:
        """Stop the ReportingAgent."""
        logger.info(f"ReportingAgent {self.agent_id} stopping...")
        await super().stop()

    async def get_health(self) -> Dict[str, Any]:
        """Get the health status of the ReportingAgent."""
        base_health = await super().get_health()
        return {
            **base_health,
            "analytics_engine_available": self.analytics_engine is not None,
            "supported_formats": ["json", "text"],
            "supported_report_types": [
                "anomaly_summary",
                "maintenance_overview", 
                "system_health"
            ]
        }

    async def register_capabilities(self) -> List[str]:
        """Register the capabilities of this agent."""
        return [
            "report_generation",
            "data_visualization",
            "kpi_calculation",
            "chart_creation"
        ]

    async def process(self) -> None:
        """Process method required by BaseAgent (placeholder for future event-driven functionality)."""
        logger.debug(f"ReportingAgent {self.agent_id} process method called")

    def generate_report(self, report_request: ReportRequest) -> ReportResult:
        """
        Generate a report based on the provided request.
        
        Args:
            report_request: The report request containing parameters
            
        Returns:
            ReportResult containing the generated report
        """
        try:
            logger.info(f"Generating report: {report_request.report_type}")
            
            # Generate unique report ID if not provided
            report_id = report_request.report_id or f"report-{uuid.uuid4().hex[:8]}"
            
            # Get analytics data
            analytics_data = self.analytics_engine.analyze(report_request)
            
            # Ensure analytics_data is not None
            if analytics_data is None:
                analytics_data = {}
            
            # Generate content based on format
            if report_request.format == "json":
                content = self._generate_json_content(analytics_data)
            else:  # text format
                content = self._generate_text_content(report_request.report_type, analytics_data)
            
            # Generate charts if requested
            charts_encoded = {}
            if report_request.include_charts and analytics_data.get("chart_data"):
                chart_b64 = self._generate_chart(analytics_data["chart_data"])
                if chart_b64:
                    charts_encoded["main_chart"] = chart_b64
            
            # Create result
            result = ReportResult(
                report_id=report_id,
                report_type=report_request.report_type,
                format=report_request.format,
                content=content,
                generated_at=datetime.utcnow(),
                charts_encoded=charts_encoded,
                metadata={
                    "parameters": report_request.parameters,
                    "time_range_start": report_request.time_range_start.isoformat() if report_request.time_range_start else None,
                    "time_range_end": report_request.time_range_end.isoformat() if report_request.time_range_end else None,
                    "include_charts": report_request.include_charts,
                    "analytics_summary": {
                        "data_points": len((analytics_data.get("chart_data") or {}).get("dates", [])),
                        "has_chart_data": bool(analytics_data.get("chart_data"))
                    }
                }
            )
            
            logger.info(f"Report {report_id} generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return ReportResult(
                report_id=report_request.report_id or f"error-{uuid.uuid4().hex[:8]}",
                report_type=report_request.report_type,
                format=report_request.format,
                content="",
                generated_at=datetime.utcnow(),
                charts_encoded={},
                metadata={},
                error_message=str(e)
            )

    def _generate_json_content(self, analytics_data: Dict[str, Any]) -> str:
        """Generate JSON formatted report content."""
        # Remove chart_data from analytics_data for JSON output (charts are separate)
        data_copy = analytics_data.copy()
        data_copy.pop("chart_data", None)
        
        return json.dumps(data_copy, indent=2, default=str)

    def _generate_text_content(self, report_type: str, analytics_data: Dict[str, Any]) -> str:
        """Generate text formatted report content."""
        # Ensure analytics_data is a dict
        if analytics_data is None:
            analytics_data = {}
            
        if report_type == "anomaly_summary":
            return self._generate_anomaly_text_report(analytics_data)
        elif report_type == "maintenance_overview":
            return self._generate_maintenance_text_report(analytics_data)
        elif report_type == "system_health":
            return self._generate_system_health_text_report(analytics_data)
        else:
            return self._generate_default_text_report(analytics_data)

    def _generate_anomaly_text_report(self, data: Dict[str, Any]) -> str:
        """Generate text format for anomaly summary report."""
        return f"""
ANOMALY SUMMARY REPORT
=====================

📊 Key Metrics:
• Total Anomalies: {data.get('total_anomalies', 'N/A')}
• Average Anomalies per Day: {data.get('avg_anomalies_per_day', 'N/A'):.2f}
• Peak Anomaly Day: {data.get('peak_anomaly_day', 'N/A')} anomalies
• Trend: {data.get('anomaly_trend', 'N/A').title()}

🔍 Analysis:
• Sensors Affected: {data.get('sensors_affected', 'N/A')}
• False Positive Rate: {data.get('false_positive_rate', 'N/A') if isinstance(data.get('false_positive_rate'), str) else f"{data.get('false_positive_rate', 0):.1%}"}

📈 Chart Data Available: {"Yes" if data.get('chart_data') else "No"}

Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

    def _generate_maintenance_text_report(self, data: Dict[str, Any]) -> str:
        """Generate text format for maintenance overview report."""
        completion_rate = (data.get('completed_tasks', 0) / data.get('total_maintenance_tasks', 1)) * 100
        
        # Format technician utilization
        tech_util = data.get('technician_utilization', 'N/A')
        tech_util_str = f"{tech_util:.1%}" if isinstance(tech_util, (int, float)) else tech_util
        
        # Format equipment uptime
        equipment_uptime = data.get('equipment_uptime', 'N/A')
        equipment_uptime_str = f"{equipment_uptime:.1%}" if isinstance(equipment_uptime, (int, float)) else equipment_uptime

        return f"""
MAINTENANCE OVERVIEW REPORT
==========================

📋 Task Summary:
• Total Tasks: {data.get('total_maintenance_tasks', 'N/A')}
• Completed: {data.get('completed_tasks', 'N/A')}
• Pending: {data.get('pending_tasks', 'N/A')}
• Overdue: {data.get('overdue_tasks', 'N/A')}
• Completion Rate: {completion_rate:.1f}%

⏱️ Performance Metrics:
• Average Completion Time: {data.get('avg_completion_time', 'N/A')} hours
• Mean Time to Repair (MTTR): {data.get('mttr_hours', 'N/A')} hours
• Technician Utilization: {tech_util_str}
• Equipment Uptime: {equipment_uptime_str}

📈 Chart Data Available: {"Yes" if data.get('chart_data') else "No"}

Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

    def _generate_system_health_text_report(self, data: Dict[str, Any]) -> str:
        """Generate text format for system health report."""
        return f"""
SYSTEM HEALTH REPORT
===================

🏥 Overall Health: {data.get('overall_system_health', 'N/A')}%

📡 Sensor Status:
• Active Sensors: {data.get('active_sensors', 'N/A')}
• Inactive Sensors: {data.get('inactive_sensors', 'N/A')}
• Sensor Availability: {(data.get('active_sensors', 0) / (data.get('active_sensors', 0) + data.get('inactive_sensors', 1))) * 100:.1f}%

⚡ Performance:
• Average Response Time: {data.get('avg_response_time_ms', 'N/A')} ms
• Data Quality Score: {data.get('data_quality_score', 'N/A') if isinstance(data.get('data_quality_score'), str) else f"{data.get('data_quality_score', 0):.1%}"}

🚨 Alerts:
• Total Alerts: {data.get('alerts_generated', 'N/A')}
• Critical Alerts: {data.get('critical_alerts', 'N/A')}

📈 Chart Data Available: {"Yes" if data.get('chart_data') else "No"}

Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

    def _generate_default_text_report(self, data: Dict[str, Any]) -> str:
        """Generate default text format report."""
        return f"""
REPORT SUMMARY
=============

Report Type: {data.get('report_type', 'Unknown')}
Data Points: {data.get('data_points', 'N/A')}
Processing Time: {data.get('processing_time_ms', 'N/A')} ms

Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

    def _generate_chart(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a matplotlib chart and return it as base64 encoded string.
        
        Args:
            chart_data: Dictionary containing chart configuration and data
            
        Returns:
            Base64 encoded chart image, or None if generation fails
        """
        try:
            if not chart_data or chart_data.get("chart_type") == "none":
                return None
                
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            chart_type = chart_data.get("chart_type", "line")
            title = chart_data.get("title", "Chart")
            xlabel = chart_data.get("xlabel", "X")
            ylabel = chart_data.get("ylabel", "Y")
            
            if chart_type == "line":
                dates = chart_data.get("dates", [])
                values = chart_data.get("anomaly_counts") or chart_data.get("uptime_percentages", [])
                
                if dates and values and len(dates) == len(values):
                    ax.plot(dates, values, marker='o', linewidth=2, markersize=4)
                    # Rotate x-axis labels for better readability
                    plt.xticks(rotation=45)
                else:
                    # Fallback to simple plot if data doesn't match
                    ax.plot([1, 2, 3, 4, 5], [1, 4, 2, 3, 5], marker='o')
                    
            elif chart_type == "bar":
                categories = chart_data.get("categories", ["A", "B", "C"])
                values = chart_data.get("values", [1, 2, 3])
                
                if len(categories) == len(values):
                    ax.bar(categories, values)
                else:
                    # Fallback bar chart
                    ax.bar(["A", "B", "C"], [1, 2, 3])
            
            # Set labels and title
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            
            # Improve layout
            plt.tight_layout()
            
            # Save to BytesIO buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # Encode to base64
            chart_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Clean up
            plt.close(fig)
            buffer.close()
            
            logger.info(f"Chart generated successfully: {chart_type}")
            return chart_b64
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            plt.close('all')  # Ensure cleanup on error
            return None
