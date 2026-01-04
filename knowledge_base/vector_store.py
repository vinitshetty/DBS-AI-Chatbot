"""
Vector Store - ChromaDB integration for document storage and retrieval
"""

import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB vector store for semantic search
    
    Features:
    - Persistent storage
    - Semantic similarity search
    - Metadata filtering
    - Batch operations
    """
    
    def __init__(self):
        from config.settings import settings
        
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        self.collection_name = settings.CHROMA_COLLECTION
        
        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = None
        
        logger.info(f"Vector store initialized at: {self.persist_directory}")
    
    async def initialize(self):
        """Initialize or load existing collection"""
        try:
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "DBS Banking Knowledge Base"}
            )
            
            doc_count = self.collection.count()
            logger.info(f"Vector store loaded: {doc_count} documents in collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
            raise
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Add documents to vector store
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique document IDs
            embeddings: List of embedding vectors
            
        Returns:
            True if successful
        """
        try:
            if not self.collection:
                await self.initialize()
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}", exc_info=True)
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents using embedding similarity
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of document dicts with content, metadata, and distance
        """
        try:
            if not self.collection:
                await self.initialize()
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Format results
            documents = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    documents.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            logger.info(f"Search returned {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a specific document by ID"""
        try:
            if not self.collection:
                await self.initialize()
            
            result = self.collection.get(ids=[doc_id])
            
            if result and result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {str(e)}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        try:
            if not self.collection:
                await self.initialize()
            
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False
    
    async def delete_collection(self) -> bool:
        """Delete entire collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            return False
    
    async def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            if not self.collection:
                await self.initialize()
            
            count = self.collection.count()
            
            return {
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}
    
    async def update_document(
        self,
        doc_id: str,
        document: str,
        metadata: Dict,
        embedding: List[float]
    ) -> bool:
        """Update an existing document"""
        try:
            if not self.collection:
                await self.initialize()
            
            self.collection.update(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            
            logger.info(f"Updated document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {str(e)}")
            return False