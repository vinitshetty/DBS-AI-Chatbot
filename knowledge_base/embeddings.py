"""
Embeddings Generator - Creates vector embeddings for text using the Mistral API.
"""
import logging
from typing import List

from mistralai.client import MistralClient as MistralAI
from config.settings import settings

logger = logging.getLogger(__name__)

class MistralEmbeddings:
    """
    A wrapper around the Mistral API for generating text embeddings.
    """

    def __init__(self):
        """
        Initializes the MistralEmbeddings client.
        """
        if not settings.MISTRAL_API_KEY or settings.MISTRAL_API_KEY == "your_mistral_api_key_here":
            logger.error("MISTRAL_API_KEY is not configured.")
            raise ValueError("MISTRAL_API_KEY must be set in your environment or settings.")

        self.client = MistralAI(api_key=settings.MISTRAL_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        logger.info(f"MistralEmbeddings initialized with model: {self.model}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: A list of documents to embed.

        Returns:
            A list of embeddings, one for each document.
        """
        try:
            # Mistral API's embeddings endpoint expects a list of strings.
            response = self.client.embeddings(model=self.model, input=texts)
            embeddings = [result.embedding for result in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings for documents: {e}", exc_info=True)
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: The query text to embed.

        Returns:
            The embedding for the query.
        """
        try:
            # Mistral API's embeddings endpoint can take a single string or a list.
            # We pass a list with one element to be consistent.
            response = self.client.embeddings(model=self.model, input=[text])
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}", exc_info=True)
            raise
