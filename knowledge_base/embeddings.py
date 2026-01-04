"""
Embeddings Generator - Creates vector embeddings for text using sentence transformers
"""

from sentence_transformers import SentenceTransformer
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingsGenerator:
    """
    Generate embeddings using Sentence Transformers
    
    Features:
    - Fast local embedding generation
    - No API calls required
    - Consistent embedding dimensions
    - Batch processing support
    """
    
    def __init__(self):
        from config.settings import settings
        
        self.model_name = settings.EMBEDDING_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully. Dimension: {self.get_dimension()}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}", exc_info=True)
            raise
    
    def generate(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text string or list of texts
            
        Returns:
            Single embedding vector or list of embedding vectors
        """
        try:
            # Handle single text input
            is_single = isinstance(texts, str)
            if is_single:
                texts = [texts]
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts, 
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Convert to list format
            if is_single:
                return embeddings[0].tolist()
            else:
                return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
            raise
    
    def generate_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings in batches for large datasets
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
            
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=show_progress
            )
            
            result = [emb.tolist() for emb in embeddings]
            logger.info(f"Successfully generated {len(result)} embeddings")
            
            return result
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}", exc_info=True)
            raise
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        try:
            return self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {str(e)}")
            return 384  # Default for all-MiniLM-L6-v2
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {str(e)}")
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find the most similar embeddings from a list of candidates
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        try:
            similarities = []
            
            for idx, candidate in enumerate(candidate_embeddings):
                sim = self.compute_similarity(query_embedding, candidate)
                similarities.append((idx, sim))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Finding similar embeddings failed: {str(e)}")
            return []