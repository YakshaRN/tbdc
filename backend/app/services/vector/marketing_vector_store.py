"""
Marketing Materials Vector Store.

Stores and searches marketing material embeddings using FAISS.
Provides semantic similarity search for lead-to-material matching.
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from loguru import logger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. Vector search will be disabled.")

from app.core.config import settings
from app.services.vector.embedding_service import embedding_service


class MarketingMaterial:
    """Represents a marketing material with its metadata."""
    
    def __init__(
        self,
        material_id: str,
        title: str,
        link: str,
        industry: str = "",
        business_topics: str = "",
        other_notes: str = "",
    ):
        self.material_id = material_id
        self.title = title
        self.link = link
        self.industry = industry
        self.business_topics = business_topics
        self.other_notes = other_notes
    
    def to_text(self) -> str:
        """Convert material to searchable text representation."""
        parts = []
        
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.industry:
            parts.append(f"Industry: {self.industry}")
        if self.business_topics:
            parts.append(f"Business Topics: {self.business_topics}")
        if self.other_notes:
            parts.append(f"Notes: {self.other_notes}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "material_id": self.material_id,
            "title": self.title,
            "link": self.link,
            "industry": self.industry,
            "business_topics": self.business_topics,
            "other_notes": self.other_notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketingMaterial":
        """Create from dictionary."""
        return cls(
            material_id=data.get("material_id", ""),
            title=data.get("title", ""),
            link=data.get("link", ""),
            industry=data.get("industry", ""),
            business_topics=data.get("business_topics", ""),
            other_notes=data.get("other_notes", ""),
        )


class MarketingVectorStore:
    """
    Vector store for marketing materials using FAISS.
    
    Features:
    - One-time indexing of marketing materials from Excel
    - Persistent storage of embeddings
    - Fast semantic similarity search
    """
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or settings.BASE_DIR / "data" / "vector_store")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.storage_dir / "marketing_index.faiss"
        self.metadata_path = self.storage_dir / "marketing_metadata.pkl"
        
        self.index: Optional[Any] = None  # FAISS index
        self.materials: List[MarketingMaterial] = []  # Material metadata
        self._loaded = False
        
        # Load existing index if available
        self._load_index()
    
    @property
    def is_available(self) -> bool:
        """Check if vector store is available."""
        return FAISS_AVAILABLE and embedding_service.is_configured
    
    @property
    def is_indexed(self) -> bool:
        """Check if materials have been indexed."""
        return self.index is not None and len(self.materials) > 0
    
    def _load_index(self) -> bool:
        """Load existing index from disk."""
        if not FAISS_AVAILABLE:
            return False
        
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, "rb") as f:
                    self.materials = pickle.load(f)
                self._loaded = True
                logger.info(f"Loaded vector index with {len(self.materials)} materials")
                return True
        except Exception as e:
            logger.error(f"Error loading vector index: {e}")
        
        return False
    
    def _save_index(self) -> bool:
        """Save index to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return False
        
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.materials, f)
            logger.info(f"Saved vector index with {len(self.materials)} materials")
            return True
        except Exception as e:
            logger.error(f"Error saving vector index: {e}")
            return False
    
    def index_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """
        Index marketing materials from Excel file.
        
        Excel columns expected:
        - Collateral Title
        - LINK
        - Industry
        - Business Topics
        - Other Notes
        
        Args:
            excel_path: Path to Excel file
            
        Returns:
            Dict with indexing results
        """
        if not FAISS_AVAILABLE:
            return {"success": False, "error": "FAISS not installed"}
        
        if not embedding_service.is_configured:
            return {"success": False, "error": "AWS not configured for embeddings"}
        
        try:
            import pandas as pd
            
            # Read Excel file
            logger.info(f"Reading Excel file: {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Normalize column names
            df.columns = df.columns.str.strip()
            
            # Map columns (handle variations in column names)
            column_mapping = {
                "Collateral Title": "title",
                "LINK": "link",
                "Industry": "industry",
                "Business Topics": "business_topics",
                "Other Notes": "other_notes",
            }
            
            materials = []
            texts = []
            
            for idx, row in df.iterrows():
                material = MarketingMaterial(
                    material_id=f"mat_{idx}",
                    title=str(row.get("Collateral Title", "")).strip(),
                    link=str(row.get("LINK", "")).strip(),
                    industry=str(row.get("Industry", "")).strip() if pd.notna(row.get("Industry")) else "",
                    business_topics=str(row.get("Business Topics", "")).strip() if pd.notna(row.get("Business Topics")) else "",
                    other_notes=str(row.get("Other Notes", "")).strip() if pd.notna(row.get("Other Notes")) else "",
                )
                
                # Skip materials without title
                if not material.title or material.title == "nan":
                    continue
                
                materials.append(material)
                texts.append(material.to_text())
            
            if not materials:
                return {"success": False, "error": "No valid materials found in Excel"}
            
            logger.info(f"Generating embeddings for {len(materials)} materials...")
            
            # Generate embeddings
            embeddings = []
            for i, text in enumerate(texts):
                embedding = embedding_service.generate_embedding(text)
                if embedding is not None:
                    embeddings.append(embedding)
                else:
                    # Use zero vector for failed embeddings
                    embeddings.append(np.zeros(embedding_service.EMBEDDING_DIMENSION, dtype=np.float32))
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(texts)} materials")
            
            # Create FAISS index
            embeddings_matrix = np.vstack(embeddings).astype(np.float32)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_matrix)
            
            # Create index (using Inner Product for cosine similarity on normalized vectors)
            dimension = embedding_service.EMBEDDING_DIMENSION
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings_matrix)
            
            self.materials = materials
            
            # Save to disk
            self._save_index()
            
            return {
                "success": True,
                "indexed_count": len(materials),
                "message": f"Successfully indexed {len(materials)} marketing materials",
            }
            
        except Exception as e:
            logger.error(f"Error indexing Excel file: {e}")
            return {"success": False, "error": str(e)}
    
    def search(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar marketing materials.
        
        Args:
            query_text: Text to search for (e.g., lead description)
            top_k: Number of results to return
            
        Returns:
            List of matching materials with scores
        """
        if not self.is_available:
            logger.warning("Vector store not available")
            return []
        
        if not self.is_indexed:
            logger.warning("No materials indexed yet")
            return []
        
        try:
            # Generate embedding for query
            query_embedding = embedding_service.generate_embedding(query_text)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Normalize for cosine similarity
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, min(top_k, len(self.materials)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.materials):
                    continue
                
                material = self.materials[idx]
                results.append({
                    "material_id": material.material_id,
                    "title": material.title,
                    "link": material.link,
                    "industry": material.industry,
                    "business_topics": material.business_topics,
                    "similarity_score": float(score),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def search_for_lead(self, lead_data: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for marketing materials relevant to a lead.
        
        Args:
            lead_data: Lead data from Zoho
            top_k: Number of results to return
            
        Returns:
            List of relevant marketing materials
        """
        # Build lead text representation
        lead_text = self._build_lead_text(lead_data)
        
        if not lead_text:
            logger.warning("Empty lead text, cannot search")
            return []
        
        return self.search(lead_text, top_k)
    
    def _build_lead_text(self, lead_data: Dict[str, Any]) -> str:
        """Build searchable text from lead data."""
        parts = []
        
        # Company info
        if lead_data.get("Company"):
            parts.append(f"Company: {lead_data['Company']}")
        
        # Industry
        if lead_data.get("Industry"):
            parts.append(f"Industry: {lead_data['Industry']}")
        
        # Description
        if lead_data.get("Description"):
            parts.append(f"Description: {lead_data['Description']}")
        
        # Title/Role
        if lead_data.get("Title"):
            parts.append(f"Role: {lead_data['Title']}")
        
        # Lead source
        if lead_data.get("Lead_Source"):
            parts.append(f"Source: {lead_data['Lead_Source']}")
        
        # Website (can indicate business type)
        if lead_data.get("Website"):
            parts.append(f"Website: {lead_data['Website']}")
        
        # Any notes or additional fields
        for key in ["Notes", "Requirements", "Pain_Points", "Use_Case"]:
            if lead_data.get(key):
                parts.append(f"{key}: {lead_data[key]}")
        
        return "\n".join(parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "is_available": self.is_available,
            "is_indexed": self.is_indexed,
            "material_count": len(self.materials) if self.materials else 0,
            "index_path": str(self.index_path),
            "faiss_available": FAISS_AVAILABLE,
            "embeddings_configured": embedding_service.is_configured,
        }
    
    def clear_index(self) -> bool:
        """Clear the index and remove stored files."""
        try:
            self.index = None
            self.materials = []
            
            if self.index_path.exists():
                os.remove(self.index_path)
            if self.metadata_path.exists():
                os.remove(self.metadata_path)
            
            logger.info("Vector index cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False


# Singleton instance
marketing_vector_store = MarketingVectorStore()
