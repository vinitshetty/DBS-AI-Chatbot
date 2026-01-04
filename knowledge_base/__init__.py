"""
Knowledge Base - RAG (Retrieval Augmented Generation) system
Manages document storage, retrieval, and embeddings
"""

# Import classes only when explicitly requested to avoid circular imports
def __getattr__(name):
    if name == 'VectorStore':
        from knowledge_base.vector_store import VectorStore
        return VectorStore
    elif name == 'EmbeddingsGenerator':
        from knowledge_base.embeddings import EmbeddingsGenerator
        return EmbeddingsGenerator
    elif name == 'RAGEngine':
        from knowledge_base.rag_engine import RAGEngine
        return RAGEngine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'VectorStore',
    'EmbeddingsGenerator',
    'RAGEngine'
]