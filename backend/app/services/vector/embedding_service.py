"""
Embedding Service using AWS Bedrock Titan Embeddings.

Generates text embeddings for semantic similarity search.
"""
import json
from typing import List, Optional
import numpy as np
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings


class EmbeddingService:
    """
    Service for generating text embeddings using AWS Bedrock Titan.
    """
    
    # Titan Embedding model
    MODEL_ID = "amazon.titan-embed-text-v1"
    EMBEDDING_DIMENSION = 1536  # Titan embedding dimension
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        """Get or create Bedrock runtime client."""
        if self._client is None:
            # If explicit credentials are provided, use them
            # Otherwise, boto3 will use IAM role credentials automatically
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            else:
                # Use default credential chain (IAM role, env vars, etc.)
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                )
        return self._client
    
    @property
    def is_configured(self) -> bool:
        """Check if Bedrock embeddings are available (via credentials or IAM role)."""
        # Cache the result after first check
        if hasattr(self, '_is_configured_cached'):
            return self._is_configured_cached
        
        try:
            # Try to create client - will use IAM role if no explicit credentials
            self._get_client()
            self._is_configured_cached = True
            logger.info("Embedding service configured and available")
            return True
        except Exception as e:
            logger.warning(f"Embedding service not available: {e}")
            self._is_configured_cached = False
            return False
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array of embedding, or None if failed
        """
        if not self.is_configured:
            logger.warning("AWS not configured, cannot generate embeddings")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
        
        try:
            client = self._get_client()
            
            # Titan embedding request format
            body = json.dumps({
                "inputText": text[:8000]  # Titan has token limit
            })
            
            response = client.invoke_model(
                modelId=self.MODEL_ID,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            if embedding:
                return np.array(embedding, dtype=np.float32)
            
            logger.warning("Empty embedding returned from Bedrock")
            return None
            
        except ClientError as e:
            logger.error(f"Bedrock embedding error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed ones)
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


# Singleton instance
embedding_service = EmbeddingService()
