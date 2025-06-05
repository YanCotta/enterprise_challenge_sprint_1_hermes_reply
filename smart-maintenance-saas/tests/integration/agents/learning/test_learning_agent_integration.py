"""
Integration tests for the Learning Agent.
"""
import pytest
import asyncio
from datetime import datetime
from typing import List

from apps.agents.learning.learning_agent import LearningAgent
from data.schemas import FeedbackData, KnowledgeItem, LearningResult
from core.events.event_models import SystemFeedbackReceivedEvent
from core.events.event_bus import EventBus


class TestLearningAgentIntegration:
    """Integration test suite for the Learning Agent."""

    @pytest.fixture
    async def event_bus(self):
        """Create a real event bus for integration testing."""
        bus = EventBus()
        yield bus
        # Cleanup
        await bus.stop()

    @pytest.fixture
    async def learning_agent(self, event_bus):
        """Create a real LearningAgent for integration testing."""
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=event_bus)
        await agent.start()
        yield agent
        await agent.stop()

    @pytest.mark.asyncio
    async def test_agent_initialization_real(self, event_bus):
        """Test real initialization of LearningAgent with actual dependencies."""
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=event_bus)
        
        # Check that components are properly initialized
        # Note: This might download the model on first run
        assert agent.chroma_client is not None
        assert agent.embedding_model is not None
        assert agent.knowledge_collection is not None
        
        # Test that collection has the correct name
        collections = agent.chroma_client.list_collections()
        collection_names = [c.name for c in collections]
        assert "maintenance_knowledge" in collection_names

    @pytest.mark.asyncio
    async def test_rag_flow_end_to_end(self, learning_agent):
        """Test the complete RAG flow with real ChromaDB and SentenceTransformer."""
        agent = learning_agent
        
        # Skip if components not initialized (e.g., in CI environment)
        if not agent.chroma_client or not agent.embedding_model:
            pytest.skip("ChromaDB or SentenceTransformer not available")
        
        # Sample maintenance knowledge documents
        documents = [
            {
                "id": "maint_doc_1",
                "content": "Regular oil changes are essential for engine health. Change oil every 3000-5000 miles.",
                "metadata": {"category": "preventive", "equipment": "engine"}
            },
            {
                "id": "maint_doc_2", 
                "content": "Check tire pressure monthly. Proper inflation improves fuel efficiency and tire life.",
                "metadata": {"category": "preventive", "equipment": "tires"}
            },
            {
                "id": "maint_doc_3",
                "content": "Clean air filters regularly to maintain engine performance and prevent damage.",
                "metadata": {"category": "preventive", "equipment": "engine"}
            }
        ]
        
        # Add documents to knowledge base
        for doc in documents:
            result = await agent.add_knowledge(
                doc_id=doc["id"],
                text_content=doc["content"],
                metadata=doc["metadata"]
            )
            assert result.knowledge_updated is True
            assert result.error_message is None
        
        # Test relevant knowledge retrieval
        query = "How to maintain engine?"
        results = await agent.retrieve_relevant_knowledge(query, n_results=2)
        
        # Verify results
        assert len(results) <= 2
        assert all(isinstance(item, KnowledgeItem) for item in results)
        
        # Results should be related to engine maintenance
        engine_related = [r for r in results if "engine" in r.description.lower()]
        assert len(engine_related) > 0
        
        # Check similarity scores are valid cosine similarity values (-1 to 1)
        for result in results:
            assert result.similarity_score is not None
            assert -1 <= result.similarity_score <= 1
        
        # Test with different query
        query2 = "tire maintenance tips"
        results2 = await agent.retrieve_relevant_knowledge(query2, n_results=1)
        
        if results2:  # If we get results
            tire_related = [r for r in results2 if "tire" in r.description.lower()]
            assert len(tire_related) > 0

    @pytest.mark.asyncio
    async def test_feedback_event_processing(self, learning_agent):
        """Test processing of SystemFeedbackReceivedEvent."""
        agent = learning_agent
        
        # Skip if components not initialized
        if not agent.chroma_client or not agent.embedding_model:
            pytest.skip("ChromaDB or SentenceTransformer not available")
        
        # Create feedback event
        feedback_data = FeedbackData(
            feedback_id="test_feedback_001",
            feedback_text="The preventive maintenance schedule worked great for our fleet. Regular checks prevented major breakdowns.",
            timestamp=datetime.now()
        )
        
        # Publish event to event bus
        event = SystemFeedbackReceivedEvent(feedback_payload=feedback_data.model_dump())
        await agent.event_bus.publish(event)
        
        # Give some time for event processing
        await asyncio.sleep(0.1)
        
        # Verify the feedback was added to knowledge base
        query_results = await agent.retrieve_relevant_knowledge(
            "preventive maintenance schedule", 
            n_results=5
        )
        
        # Check if our feedback appears in results
        feedback_found = False
        for result in query_results:
            if feedback_data.feedback_id in result.id:
                feedback_found = True
                assert "preventive maintenance" in result.description.lower()
                assert result.metadata.get("source") == "system_feedback"
                break
        
        assert feedback_found, "Feedback was not properly added to knowledge base"

    @pytest.mark.asyncio
    async def test_similarity_scoring(self, learning_agent):
        """Test that similarity scoring works correctly."""
        agent = learning_agent
        
        # Skip if components not initialized
        if not agent.chroma_client or not agent.embedding_model:
            pytest.skip("ChromaDB or SentenceTransformer not available")
        
        # Add a very specific document
        specific_doc = "Hydraulic system requires special fluid type XYZ-123 for optimal performance"
        await agent.add_knowledge(
            doc_id="hydraulic_specific",
            text_content=specific_doc,
            metadata={"specificity": "high"}
        )
        
        # Add a general document
        general_doc = "Regular maintenance is important for all equipment"
        await agent.add_knowledge(
            doc_id="general_maintenance", 
            text_content=general_doc,
            metadata={"specificity": "low"}
        )
        
        # Query for specific information
        results = await agent.retrieve_relevant_knowledge(
            "hydraulic fluid XYZ-123", 
            n_results=2
        )
        
        if len(results) >= 2:
            # The specific document should have higher similarity score
            specific_result = next((r for r in results if "hydraulic_specific" in r.id), None)
            general_result = next((r for r in results if "general_maintenance" in r.id), None)
            
            if specific_result and general_result:
                assert specific_result.similarity_score > general_result.similarity_score

    @pytest.mark.asyncio
    async def test_error_resilience(self, event_bus):
        """Test that the agent handles errors gracefully."""
        # Create agent with potential initialization issues
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=event_bus)
        
        # Even if some components fail to initialize, agent should still work
        # Test add_knowledge with failed components
        if not agent.embedding_model or not agent.knowledge_collection:
            result = await agent.add_knowledge("test_doc", "test content")
            assert result.knowledge_updated is False
            assert result.error_message is not None
        
        # Test retrieve_knowledge with failed components
        if not agent.embedding_model or not agent.knowledge_collection:
            results = await agent.retrieve_relevant_knowledge("test query")
            assert isinstance(results, list)
            assert len(results) == 0    @pytest.mark.asyncio
    async def test_large_knowledge_base(self, learning_agent):
        """Test performance with a larger knowledge base."""
        agent = learning_agent
        
        # Skip if components not initialized
        if not agent.chroma_client or not agent.embedding_model:
            pytest.skip("ChromaDB or SentenceTransformer not available")
        
        # Add multiple documents
        maintenance_topics = [
            "Engine oil maintenance and replacement procedures",
            "Brake system inspection and repair guidelines", 
            "Transmission fluid checks and servicing",
            "Air filter replacement and cleaning methods",
            "Battery maintenance and testing procedures",
            "Cooling system maintenance and troubleshooting",
            "Tire rotation and pressure monitoring",
            "Electrical system diagnostics and repair",
            "Fuel system cleaning and maintenance",
            "Suspension system inspection and adjustment"
        ]
        
        # Add all documents
        for i, topic in enumerate(maintenance_topics):
            result = await agent.add_knowledge(
                doc_id=f"maint_topic_{i:02d}",
                text_content=topic,
                metadata={"topic_id": i, "category": "maintenance_procedure"}
            )
            assert result.knowledge_updated is True
        
        # Test retrieval with various queries
        test_queries = [
            "engine maintenance",
            "brake repair", 
            "electrical diagnostics",
            "system inspection"
        ]
        
        for query in test_queries:
            results = await agent.retrieve_relevant_knowledge(query, n_results=3)
            assert len(results) <= 3
            # All results should have valid similarity scores
            for result in results:
                assert result.similarity_score is not None
                assert -1 <= result.similarity_score <= 1
