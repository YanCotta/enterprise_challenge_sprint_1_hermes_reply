"""Learning Agent implementation with RAG capabilities using ChromaDB and SentenceTransformers."""

import logging
from typing import Any, Dict, List, Optional

from apps.agents.base_agent import BaseAgent, AgentCapability
from core.events.event_models import SystemFeedbackReceivedEvent
from data.schemas import FeedbackData, KnowledgeItem, LearningResult

# Import dependencies with error handling
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class LearningAgent(BaseAgent):
    """
    Learning Agent with basic RAG capabilities using ChromaDB and SentenceTransformers.
    
    This agent stores and retrieves textual knowledge, typically from feedback,
    to support continuous system improvement and knowledge management.
    
    Key features:
    - Stores feedback and knowledge in a vector database (ChromaDB)
    - Uses SentenceTransformers for text embeddings
    - Provides semantic search and retrieval capabilities
    - Handles SystemFeedbackReceivedEvent for automated knowledge ingestion
    """

    def __init__(self, agent_id: str, event_bus: Any):
        """
        Initialize the Learning Agent with RAG capabilities.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: Event bus instance for inter-agent communication
        """
        super().__init__(agent_id, event_bus)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Initialize RAG components
        self.chroma_client = None
        self.knowledge_collection = None
        self.embedding_model = None
        
        # Initialize ChromaDB client
        try:
            if not CHROMADB_AVAILABLE:
                raise ImportError("chromadb is not available")
            
            self.chroma_client = chromadb.Client()
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name="maintenance_knowledge"
            )
            self.logger.info(f"Agent {self.agent_id}: ChromaDB client and collection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id}: Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.knowledge_collection = None
        
        # Initialize SentenceTransformer model
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("sentence-transformers is not available")
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info(f"Agent {self.agent_id}: SentenceTransformer model initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id}: Failed to initialize SentenceTransformer: {e}")
            self.embedding_model = None

    async def register_capabilities(self) -> None:
        """Register the capabilities of the Learning Agent."""
        self.capabilities.extend([
            AgentCapability(
                name="knowledge_storage",
                description="Store textual knowledge with vector embeddings for semantic retrieval",
                input_types=["FeedbackData", "text_content"],
                output_types=["LearningResult"]
            ),
            AgentCapability(
                name="knowledge_retrieval",
                description="Retrieve relevant knowledge using semantic search",
                input_types=["query_string"],
                output_types=["List[KnowledgeItem]"]
            ),
            AgentCapability(
                name="feedback_processing",
                description="Process system feedback events and store them as knowledge",
                input_types=["SystemFeedbackReceivedEvent"],
                output_types=["LearningResult"]
            )
        ])
        self.logger.info(f"Agent {self.agent_id}: Registered {len(self.capabilities)} capabilities")

    async def start(self) -> None:
        """Start the Learning Agent and subscribe to relevant events."""
        await super().start()
        
        # Subscribe to SystemFeedbackReceivedEvent
        try:
            await self.event_bus.subscribe(
                "SystemFeedbackReceivedEvent",
                self.handle_system_feedback
            )
            self.logger.info(f"Agent {self.agent_id}: Subscribed to SystemFeedbackReceivedEvent")
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id}: Failed to subscribe to events: {e}")

    async def process(self, data: Any) -> Any:
        """
        Main processing logic for the Learning Agent.
        
        Args:
            data: The data to be processed (typically feedback or query)
            
        Returns:
            Processing result based on the type of data
        """
        self.logger.debug(f"Agent {self.agent_id}: Processing data of type {type(data)}")
        
        if isinstance(data, dict):
            # Try to determine the type of processing needed
            if "feedback_text" in data:
                return await self.add_knowledge(
                    doc_id=data.get("feedback_id", "unknown"),
                    text_content=data["feedback_text"],
                    metadata=data.get("metadata", {})
                )
            elif "query" in data:
                return await self.retrieve_relevant_knowledge(
                    query=data["query"],
                    n_results=data.get("n_results", 3)
                )
        
        self.logger.warning(f"Agent {self.agent_id}: Unrecognized data format for processing")
        return None

    def _clean_metadata(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Clean metadata by removing None values, which ChromaDB doesn't accept."""
        if not metadata:
            return {}
        
        cleaned = {}
        for key, value in metadata.items():
            # ChromaDB only accepts str, int, float, or bool values
            if value is not None and isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif value is not None:
                # Convert other types to string
                cleaned[key] = str(value)
        
        return cleaned

    async def add_knowledge(self, doc_id: str, text_content: str, metadata: Optional[Dict[str, Any]] = None) -> LearningResult:
        """
        Add knowledge to the vector database.
        
        Args:
            doc_id: Unique identifier for the document/knowledge item
            text_content: The textual content to be stored
            metadata: Optional metadata to associate with the knowledge
            
        Returns:
            LearningResult indicating success or failure
        """
        self.logger.info(f"Agent {self.agent_id}: Adding knowledge with doc_id='{doc_id}'")
        
        # Check if dependencies are available
        if not self.embedding_model or not self.knowledge_collection:
            error_msg = "RAG components not properly initialized"
            self.logger.error(f"Agent {self.agent_id}: {error_msg}")
            return LearningResult(
                knowledge_updated=False,
                error_message=error_msg
            )
        
        try:
            # Generate embedding for the text content
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # Prepare metadata
            doc_metadata = self._clean_metadata(metadata)
            doc_metadata.update({
                "doc_id": doc_id,
                "text_length": len(text_content),
                "added_by_agent": self.agent_id
            })
            
            # Add to ChromaDB collection
            self.knowledge_collection.add(
                documents=[text_content],
                embeddings=[embedding],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            self.logger.info(f"Agent {self.agent_id}: Successfully added knowledge item '{doc_id}'")
            return LearningResult(
                knowledge_updated=True,
                knowledge_id=doc_id,
                metadata={"text_length": len(text_content)}
            )
            
        except Exception as e:
            error_msg = f"Failed to add knowledge: {str(e)}"
            self.logger.error(f"Agent {self.agent_id}: {error_msg}")
            return LearningResult(
                knowledge_updated=False,
                error_message=error_msg
            )

    async def retrieve_relevant_knowledge(self, query: str, n_results: int = 3) -> List[KnowledgeItem]:
        """
        Retrieve relevant knowledge using semantic search.
        
        Args:
            query: The query string for semantic search
            n_results: Maximum number of results to return
            
        Returns:
            List of KnowledgeItem objects ranked by relevance
        """
        self.logger.info(f"Agent {self.agent_id}: Retrieving knowledge for query: '{query[:50]}...'")
        
        # Check if dependencies are available
        if not self.embedding_model or not self.knowledge_collection:
            self.logger.error(f"Agent {self.agent_id}: RAG components not properly initialized")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Query the ChromaDB collection
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Transform results into KnowledgeItem objects
            knowledge_items = []
            if results['ids'] and results['ids'][0]:  # Check if we have results
                for i in range(len(results['ids'][0])):
                    # Calculate similarity score from distance (ChromaDB returns distances, lower is better)
                    distance = results['distances'][0][i] if results['distances'] else None
                    similarity_score = 1.0 - distance if distance is not None else None
                    
                    knowledge_item = KnowledgeItem(
                        id=results['ids'][0][i],
                        description=results['documents'][0][i],
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                        similarity_score=similarity_score
                    )
                    knowledge_items.append(knowledge_item)
            
            self.logger.info(f"Agent {self.agent_id}: Retrieved {len(knowledge_items)} knowledge items")
            return knowledge_items
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id}: Failed to retrieve knowledge: {e}")
            return []

    async def handle_system_feedback(self, event: SystemFeedbackReceivedEvent) -> None:
        """
        Handle SystemFeedbackReceivedEvent and store feedback as knowledge.
        
        Args:
            event: The feedback event to process
        """
        self.logger.info(f"Agent {self.agent_id}: Handling SystemFeedbackReceivedEvent {event.event_id}")
        
        try:
            # Extract feedback data from the event payload
            feedback_payload = event.feedback_payload
            
            # Convert to FeedbackData model for validation
            feedback_data = FeedbackData(**feedback_payload)
            
            # Store the feedback as knowledge
            result = await self.add_knowledge(
                doc_id=feedback_data.feedback_id,
                text_content=feedback_data.feedback_text,
                metadata={
                    "source": feedback_data.source or "system_feedback",
                    "category": feedback_data.category,
                    "timestamp": feedback_data.timestamp.isoformat(),
                    "event_id": str(event.event_id),
                    "source_agent_id": event.source_agent_id,
                    "processing_priority": event.processing_priority,
                    **feedback_data.metadata
                }
            )
            
            if result.knowledge_updated:
                self.logger.info(f"Agent {self.agent_id}: Successfully processed feedback '{feedback_data.feedback_id}'")
            else:
                self.logger.warning(f"Agent {self.agent_id}: Failed to process feedback: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id}: Error handling SystemFeedbackReceivedEvent: {e}")

    async def get_health(self) -> Dict[str, Any]:
        """
        Get the health status of the Learning Agent.
        
        Returns:
            Dictionary containing agent health information
        """
        health = await super().get_health()
        
        # Add RAG-specific health information
        health.update({
            "chromadb_available": self.chroma_client is not None,
            "embedding_model_available": self.embedding_model is not None,
            "rag_operational": self.chroma_client is not None and self.embedding_model is not None
        })
        
        # Get collection info if available
        if self.knowledge_collection:
            try:
                collection_count = self.knowledge_collection.count()
                health["knowledge_items_count"] = collection_count
            except Exception as e:
                health["collection_error"] = str(e)
        
        return health
