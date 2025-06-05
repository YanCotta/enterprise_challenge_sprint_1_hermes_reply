#!/usr/bin/env python3
"""
Learning Agent Demo Script

This script demonstrates the RAG-based LearningAgent capabilities:
1. Knowledge storage and retrieval
2. Event-driven learning from feedback
3. Semantic search functionality

Requirements:
- ChromaDB and SentenceTransformers dependencies installed
- Run from the smart-maintenance-saas directory

Usage:
    python examples/learning_agent_demo.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.agents.learning.learning_agent import LearningAgent
from core.events.event_bus import EventBus
from core.events.event_models import SystemFeedbackReceivedEvent
from data.schemas import FeedbackData


async def main():
    """Demonstrate LearningAgent functionality."""
    print("🧠 Learning Agent Demo - RAG-based Knowledge Management")
    print("=" * 60)
    
    # Initialize EventBus and LearningAgent
    event_bus = EventBus()
    learning_agent = LearningAgent(
        agent_id="demo_learning_agent",
        event_bus=event_bus
    )
    
    print("\n1️⃣ Starting Learning Agent...")
    await learning_agent.start()
    
    # Demo 1: Add initial knowledge
    print("\n2️⃣ Adding Initial Knowledge Base...")
    
    knowledge_items = [
        {
            "doc_id": "engine_maint_001",
            "text_content": "Regular engine maintenance includes oil changes every 5,000 miles, air filter replacement every 12,000 miles, and spark plug inspection every 20,000 miles. Always check engine temperature before starting maintenance.",
            "metadata": {"category": "engine", "priority": "high", "source": "manual"}
        },
        {
            "doc_id": "hydraulic_guide_001", 
            "text_content": "Hydraulic system maintenance requires checking fluid levels monthly, replacing filters every 6 months, and inspecting hoses for wear. Use only recommended hydraulic fluid type HF-150.",
            "metadata": {"category": "hydraulic", "priority": "medium", "source": "manual"}
        },
        {
            "doc_id": "electrical_safety_001",
            "text_content": "Before any electrical work, ensure power is disconnected and use proper lockout/tagout procedures. Test all circuits with a multimeter before beginning work.",
            "metadata": {"category": "electrical", "priority": "critical", "source": "safety_manual"}
        },
        {
            "doc_id": "preventive_schedule_001",
            "text_content": "Preventive maintenance schedule: daily inspections, weekly lubrication, monthly fluid checks, quarterly belt inspections, and annual overhauls for critical equipment.",
            "metadata": {"category": "preventive", "priority": "high", "source": "schedule"}
        }
    ]
    
    for item in knowledge_items:
        result = await learning_agent.add_knowledge(**item)
        if result.knowledge_updated:
            print(f"   ✅ Added: {item['doc_id']}")
        else:
            print(f"   ❌ Failed: {item['doc_id']} - {result.error_message}")
    
    # Demo 2: Semantic search queries
    print("\n3️⃣ Demonstrating Semantic Search...")
    
    queries = [
        "How to change engine oil?",
        "Hydraulic fluid maintenance",
        "Safety procedures for electrical work",
        "What is the preventive maintenance schedule?"
    ]
    
    for query in queries:
        print(f"\n📋 Query: '{query}'")
        knowledge_items = await learning_agent.retrieve_relevant_knowledge(query, n_results=2)
        
        if knowledge_items:
            for i, item in enumerate(knowledge_items, 1):
                print(f"   {i}. 📄 {item.id} (similarity: {item.similarity_score:.3f})")
                print(f"      📝 {item.description[:100]}...")
                print(f"      🏷️  Category: {item.metadata.get('category', 'N/A')}")
        else:
            print("   ❌ No relevant knowledge found")
    
    # Demo 3: Event-driven learning
    print("\n4️⃣ Demonstrating Event-Driven Learning...")
    
    # Simulate feedback events
    feedback_examples = [
        {
            "feedback_id": "feedback_001",
            "feedback_text": "Technician reported that using torque wrench set to 45 Nm for wheel bolts prevented over-tightening and improved safety.",
            "category": "best_practice",
            "source": "field_report"
        },
        {
            "feedback_id": "feedback_002", 
            "feedback_text": "Issue resolved by checking thermal cutoff switch before replacing entire motor. This saved 2 hours of downtime.",
            "category": "troubleshooting",
            "source": "maintenance_log"
        }
    ]
    
    for feedback in feedback_examples:
        print(f"\n📨 Processing feedback: {feedback['feedback_id']}")
        
        # Create feedback event
        feedback_data = FeedbackData(
            feedback_id=feedback["feedback_id"],
            feedback_text=feedback["feedback_text"],
            category=feedback["category"],
            source=feedback["source"],
            timestamp=datetime.now()
        )
        
        event = SystemFeedbackReceivedEvent(
            feedback_payload=feedback_data.model_dump()
        )
        
        # Publish event (agent should automatically process it)
        await event_bus.publish(event)
        
        # Wait a moment for processing
        await asyncio.sleep(0.1)
        
        print(f"   ✅ Feedback processed and stored as knowledge")
    
    # Demo 4: Query the newly learned knowledge
    print("\n5️⃣ Querying Newly Learned Knowledge...")
    
    new_queries = [
        "How to prevent over-tightening wheel bolts?",
        "Troubleshooting motor issues"
    ]
    
    for query in new_queries:
        print(f"\n📋 Query: '{query}'")
        knowledge_items = await learning_agent.retrieve_relevant_knowledge(query, n_results=2)
        
        for i, item in enumerate(knowledge_items, 1):
            print(f"   {i}. 📄 {item.id} (similarity: {item.similarity_score:.3f})")
            print(f"      📝 {item.description[:100]}...")
            if 'source' in item.metadata:
                print(f"      🔍 Source: {item.metadata['source']}")
    
    # Demo 5: Agent health status
    print("\n6️⃣ Agent Health Status...")
    health = await learning_agent.get_health()
    
    print(f"   🏥 Agent Status: {health['status']}")
    print(f"   🗄️  ChromaDB Available: {health['chromadb_available']}")
    print(f"   🤖 Embedding Model Available: {health['embedding_model_available']}")
    print(f"   ⚙️  RAG Operational: {health['rag_operational']}")
    if 'knowledge_items_count' in health:
        print(f"   📊 Knowledge Items Stored: {health['knowledge_items_count']}")
    
    # Cleanup
    print("\n7️⃣ Stopping Learning Agent...")
    await learning_agent.stop()
    await event_bus.stop()
    
    print("\n🎉 Demo Complete!")
    print("\nThe LearningAgent demonstrated:")
    print("  • RAG-based knowledge storage and retrieval")
    print("  • Semantic search with similarity scoring")
    print("  • Event-driven learning from feedback")
    print("  • Persistent knowledge across sessions")
    print("  • Comprehensive health monitoring")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
