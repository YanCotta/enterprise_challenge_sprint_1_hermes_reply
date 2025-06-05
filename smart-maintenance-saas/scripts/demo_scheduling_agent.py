#!/usr/bin/env python3
"""
Demonstration script for the SchedulingAgent - Day 8 of Smart Maintenance SaaS.

This script demonstrates:
1. SchedulingAgent initialization and startup
2. MaintenancePredictedEvent handling
3. Automatic scheduling with optimization
4. MaintenanceScheduledEvent publishing
5. Error handling scenarios
6. Integration with the event bus system

Run this script to see the SchedulingAgent in action.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from apps.agents.decision.scheduling_agent import SchedulingAgent
from core.events.event_bus import EventBus
from core.events.event_models import MaintenancePredictedEvent


def setup_logging():
    """Configure logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s (%(name)s)',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


async def demo_basic_scheduling():
    """Demonstrate basic scheduling functionality."""
    print("\n" + "="*80)
    print("DEMO 1: Basic Maintenance Scheduling")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_scheduling_agent", event_bus)
    await scheduling_agent.start()
    
    # Create a sample prediction event
    prediction_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id="demo_pump_001",
        predicted_failure_date=datetime.utcnow() + timedelta(days=10),
        confidence_interval_lower=datetime.utcnow() + timedelta(days=7),
        confidence_interval_upper=datetime.utcnow() + timedelta(days=13),
        prediction_confidence=0.87,
        time_to_failure_days=10.0,
        maintenance_type="preventive",
        prediction_method="prophet",
        historical_data_points=150,
        model_metrics={"mae": 0.08, "rmse": 0.12},
        recommended_actions=["inspect_bearings", "check_lubrication", "test_vibration"],
        agent_id="demo_prediction_agent"
    )
    
    print(f"📅 Publishing MaintenancePredictedEvent for equipment: {prediction_event.equipment_id}")
    print(f"   - Predicted failure: {prediction_event.predicted_failure_date}")
    print(f"   - Time to failure: {prediction_event.time_to_failure_days} days")
    print(f"   - Maintenance type: {prediction_event.maintenance_type}")
    print(f"   - Confidence: {prediction_event.prediction_confidence:.2%}")
    
    # Publish the event
    await event_bus.publish("MaintenancePredictedEvent", prediction_event.dict())
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Cleanup
    await scheduling_agent.stop()
    await event_bus.stop()
    
    print("✅ Basic scheduling demo completed!")


async def demo_multiple_equipment_scheduling():
    """Demonstrate scheduling for multiple equipment pieces."""
    print("\n" + "="*80)
    print("DEMO 2: Multiple Equipment Scheduling")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_multi_scheduling_agent", event_bus)
    await scheduling_agent.start()
    
    # Create multiple prediction events with different priorities
    equipment_data = [
        {
            "equipment_id": "critical_turbine_001",
            "days_to_failure": 3,  # Critical - 3 days
            "maintenance_type": "corrective",
            "confidence": 0.95
        },
        {
            "equipment_id": "hvac_unit_002", 
            "days_to_failure": 45,  # Medium priority - 45 days
            "maintenance_type": "preventive",
            "confidence": 0.78
        },
        {
            "equipment_id": "conveyor_motor_003",
            "days_to_failure": 15,  # High priority - 15 days
            "maintenance_type": "inspection",
            "confidence": 0.82
        },
        {
            "equipment_id": "backup_generator_004",
            "days_to_failure": 120,  # Low priority - 120 days
            "maintenance_type": "preventive",
            "confidence": 0.71
        }
    ]
    
    print(f"📊 Scheduling maintenance for {len(equipment_data)} equipment pieces:")
    
    for equipment in equipment_data:
        prediction_event = MaintenancePredictedEvent(
            original_anomaly_event_id=uuid4(),
            equipment_id=equipment["equipment_id"],
            predicted_failure_date=datetime.utcnow() + timedelta(days=equipment["days_to_failure"]),
            confidence_interval_lower=datetime.utcnow() + timedelta(days=equipment["days_to_failure"] - 2),
            confidence_interval_upper=datetime.utcnow() + timedelta(days=equipment["days_to_failure"] + 2),
            prediction_confidence=equipment["confidence"],
            time_to_failure_days=float(equipment["days_to_failure"]),
            maintenance_type=equipment["maintenance_type"],
            historical_data_points=100,
            agent_id="demo_prediction_agent"
        )
        
        print(f"   🔧 {equipment['equipment_id']}: {equipment['days_to_failure']} days, {equipment['maintenance_type']}")
        
        # Publish the event
        await event_bus.publish("MaintenancePredictedEvent", prediction_event.dict())
        
        # Small delay between events
        await asyncio.sleep(0.1)
    
    # Wait for all processing to complete
    await asyncio.sleep(1.0)
    
    # Cleanup
    await scheduling_agent.stop()
    await event_bus.stop()
    
    print("✅ Multiple equipment scheduling demo completed!")


async def demo_scheduling_constraints():
    """Demonstrate scheduling with various constraints."""
    print("\n" + "="*80)
    print("DEMO 3: Scheduling with Constraints")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_constraints_agent", event_bus)
    await scheduling_agent.start()
    
    # Test 1: Equipment requiring specialized skills
    print("🎯 Test 1: Equipment requiring specialized skills")
    specialized_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id="quantum_processor_001",  # Requires specialized skills
        predicted_failure_date=datetime.utcnow() + timedelta(days=8),
        confidence_interval_lower=datetime.utcnow() + timedelta(days=6),
        confidence_interval_upper=datetime.utcnow() + timedelta(days=10),
        prediction_confidence=0.91,
        time_to_failure_days=8.0,
        maintenance_type="corrective",
        historical_data_points=75,
        agent_id="demo_prediction_agent"
    )
    
    # Create a maintenance request manually to test skill matching
    request = scheduling_agent._create_maintenance_request(specialized_event)
    request.required_skills = ["quantum_mechanics", "laser_physics"]  # No technician has these skills
    
    print(f"   Equipment: {request.equipment_id}")
    print(f"   Required skills: {request.required_skills}")
    
    schedule = await scheduling_agent.schedule_maintenance_task(request)
    print(f"   Scheduling result: {schedule.status}")
    if schedule.constraints_violated:
        print(f"   Constraints violated: {schedule.constraints_violated}")
    
    # Test 2: Normal equipment with available technicians
    print("\n🎯 Test 2: Equipment with available technicians")
    normal_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id="standard_pump_002",
        predicted_failure_date=datetime.utcnow() + timedelta(days=12),
        confidence_interval_lower=datetime.utcnow() + timedelta(days=10),
        confidence_interval_upper=datetime.utcnow() + timedelta(days=14),
        prediction_confidence=0.85,
        time_to_failure_days=12.0,
        maintenance_type="preventive",
        historical_data_points=120,
        agent_id="demo_prediction_agent"
    )
    
    await event_bus.publish("MaintenancePredictedEvent", normal_event.dict())
    await asyncio.sleep(0.5)
    
    # Cleanup
    await scheduling_agent.stop()
    await event_bus.stop()
    
    print("✅ Scheduling constraints demo completed!")


async def demo_optimization_scoring():
    """Demonstrate the optimization scoring algorithm."""
    print("\n" + "="*80)
    print("DEMO 4: Optimization Scoring Algorithm")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_optimization_agent", event_bus)
    await scheduling_agent.start()
    
    # Import mock technicians for demonstration
    from apps.agents.decision.scheduling_agent import mock_technicians
    
    print("👥 Available Technicians:")
    for tech in mock_technicians:
        print(f"   {tech['id']}: {tech['name']}")
        print(f"      Skills: {tech['skills']}")
        print(f"      Experience: {tech['experience_years']} years")
        print(f"      Availability score: {tech['availability_score']:.1%}")
        print()
    
    # Create a maintenance request
    prediction_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id="optimization_test_motor",
        predicted_failure_date=datetime.utcnow() + timedelta(days=20),
        confidence_interval_lower=datetime.utcnow() + timedelta(days=18),
        confidence_interval_upper=datetime.utcnow() + timedelta(days=22),
        prediction_confidence=0.83,
        time_to_failure_days=20.0,
        maintenance_type="preventive",
        historical_data_points=90,
        agent_id="demo_prediction_agent"
    )
    
    request = scheduling_agent._create_maintenance_request(prediction_event)
    print(f"🔧 Maintenance Request:")
    print(f"   Equipment: {request.equipment_id}")
    print(f"   Required skills: {request.required_skills}")
    print(f"   Priority: {request.priority}")
    print(f"   Estimated duration: {request.estimated_duration_hours} hours")
    
    # Test optimization scoring for each technician
    print("\n📊 Optimization Scores by Technician:")
    start_time = datetime.utcnow() + timedelta(days=1, hours=9)  # Tomorrow at 9 AM
    end_time = start_time + timedelta(hours=request.estimated_duration_hours)
    
    for tech in mock_technicians:
        score = scheduling_agent._calculate_optimization_score(request, tech, start_time, end_time)
        print(f"   {tech['name']}: {score:.3f}")
        
        # Show matching skills
        matching_skills = set(request.required_skills) & set(tech['skills'])
        if matching_skills:
            print(f"      ✓ Matching skills: {list(matching_skills)}")
        else:
            print(f"      ✗ No matching skills")
    
    # Cleanup
    await scheduling_agent.stop()
    await event_bus.stop()
    
    print("✅ Optimization scoring demo completed!")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "="*80)
    print("DEMO 5: Error Handling")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_error_agent", event_bus)
    await scheduling_agent.start()
    
    # Test 1: Malformed event data
    print("🚨 Test 1: Malformed event data")
    malformed_data = {
        "equipment_id": "malformed_equipment",
        "some_invalid_field": "invalid_value"
        # Missing required fields
    }
    
    await event_bus.publish("MaintenancePredictedEvent", malformed_data)
    await asyncio.sleep(0.3)
    
    # Verify agent is still running
    health = await scheduling_agent.get_health()
    print(f"   Agent status after error: {health['status']}")
    
    # Test 2: Edge case - very short time to failure
    print("\n🚨 Test 2: Very short time to failure (emergency)")
    emergency_event = MaintenancePredictedEvent(
        original_anomaly_event_id=uuid4(),
        equipment_id="emergency_turbine_001",
        predicted_failure_date=datetime.utcnow() + timedelta(hours=2),  # Only 2 hours!
        confidence_interval_lower=datetime.utcnow() + timedelta(hours=1),
        confidence_interval_upper=datetime.utcnow() + timedelta(hours=3),
        prediction_confidence=0.98,
        time_to_failure_days=0.083,  # ~2 hours in days
        maintenance_type="corrective",
        historical_data_points=50,
        agent_id="demo_prediction_agent"
    )
    
    await event_bus.publish("MaintenancePredictedEvent", emergency_event.dict())
    await asyncio.sleep(0.3)
    
    # Cleanup
    await scheduling_agent.stop()
    await event_bus.stop()
    
    print("✅ Error handling demo completed!")


async def demo_agent_health_monitoring():
    """Demonstrate agent health monitoring."""
    print("\n" + "="*80)
    print("DEMO 6: Agent Health Monitoring")
    print("="*80)
    
    # Create event bus and agent
    event_bus = EventBus()
    await event_bus.start()
    
    scheduling_agent = SchedulingAgent("demo_health_agent", event_bus)
    
    # Check health before start
    print("🏥 Health check before starting:")
    try:
        health = await scheduling_agent.get_health()
        print(f"   Status: {health['status']}")
        print(f"   Timestamp: {health['timestamp']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Start the agent
    await scheduling_agent.start()
    
    # Check health after start
    print("\n🏥 Health check after starting:")
    health = await scheduling_agent.get_health()
    print(f"   Agent ID: {health['agent_id']}")
    print(f"   Status: {health['status']}")
    print(f"   Timestamp: {health['timestamp']}")
    print(f"   Capabilities: {len(scheduling_agent.capabilities)} registered")
    
    # Show capabilities
    print("\n🎯 Agent Capabilities:")
    for i, capability in enumerate(scheduling_agent.capabilities, 1):
        print(f"   {i}. {capability.name}")
        print(f"      Description: {capability.description}")
        print(f"      Input types: {capability.input_types}")
        print(f"      Output types: {capability.output_types}")
    
    # Stop the agent
    await scheduling_agent.stop()
    
    # Check health after stop
    print("\n🏥 Health check after stopping:")
    health = await scheduling_agent.get_health()
    print(f"   Status: {health['status']}")
    
    # Cleanup
    await event_bus.stop()
    
    print("✅ Agent health monitoring demo completed!")


async def main():
    """Run all demonstration scenarios."""
    setup_logging()
    
    print("🚀 Starting SchedulingAgent Demonstration")
    print("This demo showcases the Day 8 SchedulingAgent implementation")
    print("for the Smart Maintenance SaaS platform.")
    
    try:
        # Run all demos
        await demo_basic_scheduling()
        await demo_multiple_equipment_scheduling()
        await demo_scheduling_constraints()
        await demo_optimization_scoring()
        await demo_error_handling()
        await demo_agent_health_monitoring()
        
        print("\n" + "="*80)
        print("🎉 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✅ Event-driven maintenance scheduling")
        print("✅ Priority-based task scheduling")
        print("✅ Technician skill matching")
        print("✅ Optimization scoring algorithm")
        print("✅ Constraint satisfaction")
        print("✅ Error handling and resilience")
        print("✅ Health monitoring and status reporting")
        print("✅ Integration with event bus system")
        
        print("\nNext Steps:")
        print("🔧 Integrate OR-Tools for advanced optimization")
        print("📅 Connect to real calendar systems (Google Calendar, Outlook)")
        print("👥 Add dynamic technician availability tracking")
        print("📊 Implement scheduling analytics and reporting")
        print("🔄 Add rescheduling capabilities for changed priorities")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
