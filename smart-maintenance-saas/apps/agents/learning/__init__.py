"""Learning agent module for RAG-based knowledge management and continuous system improvement."""

import os

# Only import LearningAgent if ChromaDB is not disabled
if os.getenv('DISABLE_CHROMADB', '').lower() != 'true':
    try:
        from .learning_agent import LearningAgent
        __all__ = ["LearningAgent"]
    except ImportError:
        # If import fails, provide a dummy class
        class LearningAgent:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("LearningAgent is not available (ChromaDB dependency missing)")
        __all__ = ["LearningAgent"]
else:
    # Provide a dummy class when ChromaDB is disabled
    class LearningAgent:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("LearningAgent is disabled (DISABLE_CHROMADB=true)")
    __all__ = ["LearningAgent"]
