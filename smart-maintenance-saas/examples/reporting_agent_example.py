#!/usr/bin/env python3
"""
Example usage of the ReportingAgent for generating analytics reports.

This script demonstrates how to:
1. Initialize a ReportingAgent
2. Generate different types of reports (JSON and text formats)
3. Handle charts and visualizations
4. Work with time ranges and custom parameters

Requirements:
- Run from the smart-maintenance-saas directory
- Ensure all dependencies are installed via Poetry
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from core.events.event_bus import EventBus
from apps.agents.decision.reporting_agent import ReportingAgent
from data.schemas import ReportRequest


async def main():
    """Demonstrate ReportingAgent capabilities."""
    print("🚀 ReportingAgent Example - Generating Analytics Reports\n")
    
    # Initialize the EventBus and ReportingAgent
    event_bus = EventBus()
    reporting_agent = ReportingAgent(
        agent_id="demo-reporting-agent",
        event_bus=event_bus
    )
    
    print(f"✅ ReportingAgent initialized: {reporting_agent.agent_id}")
    print(f"📊 Agent capabilities: {reporting_agent.capabilities}\n")
    
    # Start the agent
    await reporting_agent.start()
    health_status = await reporting_agent.get_health()
    print(f"🔄 Agent status: {health_status['status']}\n")
    
    # Example 1: Generate an Anomaly Summary Report (JSON format)
    print("=" * 60)
    print("📈 Example 1: Anomaly Summary Report (JSON)")
    print("=" * 60)
    
    anomaly_request = ReportRequest(
        report_type="anomaly_summary",
        format="json",
        include_charts=True,
        time_range_start=datetime.now() - timedelta(days=7),
        time_range_end=datetime.now(),
        parameters={"confidence_threshold": 0.8}
    )
    
    anomaly_result = reporting_agent.generate_report(anomaly_request)
    
    print(f"📋 Report ID: {anomaly_result.report_id}")
    print(f"📅 Generated at: {anomaly_result.generated_at}")
    print(f"📊 Report Type: {anomaly_result.report_type}")
    print(f"📄 Format: {anomaly_result.format}")
    print(f"📈 Charts included: {len(anomaly_result.charts_encoded) if anomaly_result.charts_encoded else 0}")
    
    if anomaly_result.charts_encoded:
        print(f"🖼️  Chart types: {list(anomaly_result.charts_encoded.keys())}")
    
    print("\n")
    
    # Example 2: Generate a Maintenance Overview Report (Text format)
    print("=" * 60)
    print("📝 Example 2: Maintenance Overview Report (Text)")
    print("=" * 60)
    
    maintenance_request = ReportRequest(
        report_type="maintenance_overview",
        format="text",
        include_charts=True,
        time_range_start=datetime.now() - timedelta(days=30),
        time_range_end=datetime.now()
    )
    
    maintenance_result = reporting_agent.generate_report(maintenance_request)
    
    print(f"📋 Report ID: {maintenance_result.report_id}")
    print(f"📊 Report Type: {maintenance_result.report_type}")
    print("📄 Report Content Preview:")
    print("-" * 40)
    # Show first 500 characters of the text content
    content_preview = maintenance_result.content[:500] + "..." if len(maintenance_result.content) > 500 else maintenance_result.content
    print(content_preview)
    print("-" * 40)
    print("\n")
    
    # Example 3: Generate a System Health Report without charts
    print("=" * 60)
    print("🏥 Example 3: System Health Report (No Charts)")
    print("=" * 60)
    
    health_request = ReportRequest(
        report_type="system_health",
        format="json",
        include_charts=False,
        time_range_start=datetime.now() - timedelta(hours=24),
        time_range_end=datetime.now(),
        parameters={"include_details": True}
    )
    
    health_result = reporting_agent.generate_report(health_request)
    
    print(f"📋 Report ID: {health_result.report_id}")
    print(f"📊 Report Type: {health_result.report_type}")
    print(f"📄 Format: {health_result.format}")
    print(f"📈 Charts included: {len(health_result.charts_encoded) if health_result.charts_encoded else 0}")
    print("\n")
    
    # Example 4: Demonstrate error handling with invalid report type
    print("=" * 60)
    print("⚠️  Example 4: Error Handling (Invalid Report Type)")
    print("=" * 60)
    
    try:
        invalid_request = ReportRequest(
            report_type="invalid_report_type",
            format="json",
            include_charts=False
        )
        
        invalid_result = reporting_agent.generate_report(invalid_request)
        print(f"📋 Report ID: {invalid_result.report_id}")
        print(f"📊 Report Type: {invalid_result.report_type}")
        print(f"⚠️  Error: {invalid_result.error_message or 'No error message'}")
        print("✅ Error handled gracefully - report still generated with default analytics")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n")
    
    # Example 5: Performance demonstration
    print("=" * 60)
    print("⚡ Example 5: Performance Test (Multiple Reports)")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Generate multiple reports concurrently
    results = []
    for i in range(3):
        request = ReportRequest(
            report_type=["anomaly_summary", "maintenance_overview", "system_health"][i],
            format="json",
            include_charts=True,
            report_id=f"perf-test-{i+1}"
        )
        result = reporting_agent.generate_report(request)
        results.append(result)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"⏱️  Generated {len(results)} reports in {duration:.2f} seconds")
    print(f"📊 Average time per report: {duration/len(results):.2f} seconds")
    
    for i, result in enumerate(results):
        print(f"   📋 Report {i+1}: {result.report_id} - {result.report_type}")
    
    print("\n")
    
    # Stop the agent
    await reporting_agent.stop()
    final_health = await reporting_agent.get_health()
    print(f"🛑 Agent stopped. Final status: {final_health['status']}")
    
    print("\n🎉 ReportingAgent example completed successfully!")
    print("💡 Try integrating these reports into dashboards or APIs for real-time analytics.")


if __name__ == "__main__":
    asyncio.run(main())
