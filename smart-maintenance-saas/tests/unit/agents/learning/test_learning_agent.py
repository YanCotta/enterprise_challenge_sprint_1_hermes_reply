"""
Unit tests for the Learning Agent.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from apps.agents.learning.learning_agent import LearningAgent
from data.schemas import FeedbackData, KnowledgeItem, LearningResult
from core.events.event_models import SystemFeedbackReceivedEvent


class TestLearningAgent:
    """Test suite for the Learning Agent."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus."""
        return AsyncMock()

    @pytest.fixture
    def mock_chromadb_client(self):
        """Create a mock ChromaDB client."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        return mock_client, mock_collection

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Create a mock SentenceTransformer."""
        mock_transformer = Mock()
        # Create a mock that behaves like a numpy array with tolist() method
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_transformer.encode.return_value = mock_embedding
        return mock_transformer

    @patch('apps.agents.learning.learning_agent.chromadb.Client')
    @patch('apps.agents.learning.learning_agent.SentenceTransformer')
    def test_init_success(self, mock_sentence_transformer_class, mock_chromadb_class, 
                         mock_event_bus, mock_chromadb_client, mock_sentence_transformer):
        """Test successful initialization of LearningAgent."""
        # Setup mocks
        mock_chromadb_class.return_value = mock_chromadb_client[0]
        mock_sentence_transformer_class.return_value = mock_sentence_transformer
        
        # Create agent
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
        
        # Verify initialization
        assert agent.chroma_client is not None
        assert agent.embedding_model is not None
        assert agent.knowledge_collection is not None
        mock_chromadb_class.assert_called_once()
        mock_sentence_transformer_class.assert_called_once_with('all-MiniLM-L6-v2')
        mock_chromadb_client[0].get_or_create_collection.assert_called_once_with(
            name="maintenance_knowledge"
        )

    @patch('apps.agents.learning.learning_agent.chromadb.Client')
    @patch('apps.agents.learning.learning_agent.SentenceTransformer')
    def test_init_chromadb_failure(self, mock_sentence_transformer_class, mock_chromadb_class, 
                                  mock_event_bus, mock_sentence_transformer):
        """Test initialization failure when ChromaDB client creation fails."""
        # Setup mocks to raise exception
        mock_chromadb_class.side_effect = Exception("ChromaDB connection failed")
        mock_sentence_transformer_class.return_value = mock_sentence_transformer
        
        # Create agent
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
        
        # Verify fallback behavior
        assert agent.chroma_client is None
        assert agent.embedding_model is not None
        assert agent.knowledge_collection is None

    @patch('apps.agents.learning.learning_agent.chromadb.Client')
    @patch('apps.agents.learning.learning_agent.SentenceTransformer')
    def test_init_sentence_transformer_failure(self, mock_sentence_transformer_class, 
                                              mock_chromadb_class, mock_event_bus, 
                                              mock_chromadb_client):
        """Test initialization failure when SentenceTransformer creation fails."""
        # Setup mocks
        mock_chromadb_class.return_value = mock_chromadb_client[0]
        mock_sentence_transformer_class.side_effect = Exception("Model download failed")
        
        # Create agent
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
        
        # Verify fallback behavior
        assert agent.chroma_client is not None
        assert agent.embedding_model is None
        assert agent.knowledge_collection is not None

    @pytest.fixture
    def learning_agent_with_mocks(self, mock_event_bus):
        """Create a LearningAgent with mocked dependencies."""
        with patch('apps.agents.learning.learning_agent.chromadb.Client') as mock_chromadb_class, \
             patch('apps.agents.learning.learning_agent.SentenceTransformer') as mock_sentence_transformer_class:
            
            # Setup mocks
            mock_client = Mock()
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chromadb_class.return_value = mock_client
            
            mock_transformer = Mock()
            # Create a mock that behaves like a numpy array with tolist() method
            mock_embedding = Mock()
            mock_embedding.tolist.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_transformer.encode.return_value = mock_embedding
            mock_sentence_transformer_class.return_value = mock_transformer
            
            agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
            agent.mock_collection = mock_collection
            agent.mock_transformer = mock_transformer
            
            return agent

    @pytest.mark.asyncio
    async def test_add_knowledge_success(self, learning_agent_with_mocks):
        """Test successful knowledge addition."""
        agent = learning_agent_with_mocks
        
        # Test data
        doc_id = "test_doc_1"
        text_content = "This is test maintenance knowledge"
        metadata = {"source": "feedback", "category": "maintenance"}
        
        # Call method
        result = await agent.add_knowledge(doc_id, text_content, metadata)
        
        # Verify calls
        agent.mock_transformer.encode.assert_called_once_with(text_content)
        agent.mock_collection.add.assert_called_once_with(
            documents=[text_content],
            embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],
            metadatas=[{
                "source": "feedback", 
                "category": "maintenance",
                "doc_id": doc_id,
                "text_length": len(text_content),
                "added_by_agent": "test_learning_agent"
            }],
            ids=[doc_id]
        )
        
        # Verify result
        assert isinstance(result, LearningResult)
        assert result.knowledge_updated is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_add_knowledge_no_metadata(self, learning_agent_with_mocks):
        """Test knowledge addition without metadata."""
        agent = learning_agent_with_mocks
        
        # Test data
        doc_id = "test_doc_2"
        text_content = "Another test knowledge"
        
        # Call method
        result = await agent.add_knowledge(doc_id, text_content)
        
        # Verify calls
        agent.mock_collection.add.assert_called_once_with(
            documents=[text_content],
            embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],
            metadatas=[{
                "doc_id": doc_id,
                "text_length": len(text_content),
                "added_by_agent": "test_learning_agent"
            }],
            ids=[doc_id]
        )
        
        # Verify result
        assert result.knowledge_updated is True

    @pytest.mark.asyncio
    async def test_add_knowledge_failure(self, learning_agent_with_mocks):
        """Test knowledge addition failure."""
        agent = learning_agent_with_mocks
        
        # Setup mock to raise exception
        agent.mock_collection.add.side_effect = Exception("Database error")
        
        # Test data
        doc_id = "test_doc_3"
        text_content = "Test knowledge that will fail"
        
        # Call method
        result = await agent.add_knowledge(doc_id, text_content)
        
        # Verify result
        assert isinstance(result, LearningResult)
        assert result.knowledge_updated is False
        assert "Database error" in result.error_message

    @pytest.mark.asyncio
    async def test_add_knowledge_no_components(self, mock_event_bus):
        """Test knowledge addition when components are not initialized."""
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
        agent.embedding_model = None
        agent.knowledge_collection = None
        
        # Call method
        result = await agent.add_knowledge("test_doc", "test content")
        
        # Verify result
        assert result.knowledge_updated is False
        assert "not properly initialized" in result.error_message

    @pytest.mark.asyncio
    async def test_retrieve_relevant_knowledge_success(self, learning_agent_with_mocks):
        """Test successful knowledge retrieval."""
        agent = learning_agent_with_mocks
        
        # Setup mock query response
        mock_response = {
            'ids': [['doc1', 'doc2']],
            'documents': [['First document', 'Second document']],
            'metadatas': [[{'source': 'feedback'}, {'source': 'manual'}]],
            'distances': [[0.1, 0.3]]
        }
        agent.mock_collection.query.return_value = mock_response
        
        # Call method
        query = "test query"
        n_results = 2
        results = await agent.retrieve_relevant_knowledge(query, n_results)
        
        # Verify calls
        agent.mock_transformer.encode.assert_called_once_with(query)
        agent.mock_collection.query.assert_called_once_with(
            query_embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],
            n_results=n_results
        )
        
        # Verify results
        assert len(results) == 2
        assert all(isinstance(item, KnowledgeItem) for item in results)
        
        # Check first result
        assert results[0].id == 'doc1'
        assert results[0].description == 'First document'
        assert results[0].metadata == {'source': 'feedback'}
        assert results[0].similarity_score == pytest.approx(0.9, rel=1e-2)  # 1 - 0.1
        
        # Check second result
        assert results[1].id == 'doc2'
        assert results[1].similarity_score == pytest.approx(0.7, rel=1e-2)  # 1 - 0.3

    @pytest.mark.asyncio
    async def test_retrieve_relevant_knowledge_empty_results(self, learning_agent_with_mocks):
        """Test knowledge retrieval with empty results."""
        agent = learning_agent_with_mocks
        
        # Setup mock query response with empty results
        mock_response = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        agent.mock_collection.query.return_value = mock_response
        
        # Call method
        results = await agent.retrieve_relevant_knowledge("test query")
        
        # Verify results
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_relevant_knowledge_no_components(self, mock_event_bus):
        """Test knowledge retrieval when components are not initialized."""
        agent = LearningAgent(agent_id="test_learning_agent", event_bus=mock_event_bus)
        agent.embedding_model = None
        agent.knowledge_collection = None
        
        # Call method
        results = await agent.retrieve_relevant_knowledge("test query")
        
        # Verify empty results
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_handle_system_feedback(self, learning_agent_with_mocks):
        """Test handling of system feedback events."""
        agent = learning_agent_with_mocks
        
        # Mock add_knowledge method
        agent.add_knowledge = AsyncMock(return_value=LearningResult(knowledge_updated=True))
        
        # Create test event
        feedback_data = FeedbackData(
            feedback_id="fb_123",
            feedback_text="Great maintenance job!",
            timestamp=datetime.now()
        )
        event = SystemFeedbackReceivedEvent(feedback_payload=feedback_data.model_dump())
        
        # Call handler
        await agent.handle_system_feedback(event)
        
        # Verify add_knowledge was called correctly
        # The metadata should include all feedback and event fields
        expected_call = agent.add_knowledge.call_args
        assert expected_call[1]["doc_id"] == "fb_123"
        assert expected_call[1]["text_content"] == "Great maintenance job!"
        
        metadata = expected_call[1]["metadata"]
        assert metadata["timestamp"] == feedback_data.timestamp.isoformat()
        assert "event_id" in metadata
        assert metadata["source"] == "system_feedback"  # Default when FeedbackData.source is None
        assert metadata["category"] is None  # Default value from FeedbackData

    @pytest.mark.asyncio
    async def test_start_method_subscribes_to_events(self, learning_agent_with_mocks):
        """Test that the start method subscribes to the correct events."""
        agent = learning_agent_with_mocks
        
        # Call start method
        await agent.start()
        
        # Verify event subscription
        agent.event_bus.subscribe.assert_called_once_with(
            "SystemFeedbackReceivedEvent",
            agent.handle_system_feedback
        )
