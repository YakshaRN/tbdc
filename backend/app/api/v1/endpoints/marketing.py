"""
Marketing Materials endpoints.

Provides:
- Upload and index marketing materials from Excel
- Search for relevant materials
- Get vector store status
"""
import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from app.services.vector.marketing_vector_store import marketing_vector_store
from app.core.config import settings

router = APIRouter()

# Directory for uploaded files
UPLOAD_DIR = settings.BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/index")
async def index_marketing_materials(
    file: UploadFile = File(..., description="Excel file with marketing materials"),
):
    """
    Upload and index marketing materials from Excel file.
    
    Expected Excel columns:
    - Collateral Title: Title of the marketing material
    - LINK: URL/link to the material
    - Industry: Target industry
    - Business Topics: Relevant business topics
    - Other Notes: Additional notes
    
    This is a one-time operation. Re-uploading will replace the existing index.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded file saved: {file_path}")
        
        # Index the materials
        result = marketing_vector_store.index_from_excel(str(file_path))
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": result["message"],
                    "indexed_count": result["indexed_count"],
                    "file": file.filename,
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Indexing failed: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded file
        if file_path.exists():
            os.remove(file_path)


@router.get("/search")
async def search_marketing_materials(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return"),
):
    """
    Search for marketing materials by text query.
    
    Uses semantic similarity to find the most relevant materials.
    """
    if not marketing_vector_store.is_available:
        raise HTTPException(
            status_code=503,
            detail="Vector search not available. Check AWS configuration."
        )
    
    if not marketing_vector_store.is_indexed:
        raise HTTPException(
            status_code=404,
            detail="No marketing materials indexed yet. Upload an Excel file first."
        )
    
    results = marketing_vector_store.search(query, top_k)
    
    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


@router.get("/status")
async def get_vector_store_status():
    """
    Get the status of the marketing materials vector store.
    """
    stats = marketing_vector_store.get_stats()
    return stats


@router.delete("/clear")
async def clear_marketing_index():
    """
    Clear the marketing materials index.
    
    This will remove all indexed materials. You'll need to re-upload
    the Excel file to rebuild the index.
    """
    success = marketing_vector_store.clear_index()
    
    if success:
        return {"message": "Marketing materials index cleared successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to clear index"
        )


@router.get("/materials")
async def list_indexed_materials(
    limit: int = Query(50, ge=1, le=200, description="Maximum materials to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List all indexed marketing materials.
    """
    if not marketing_vector_store.is_indexed:
        return {
            "materials": [],
            "total": 0,
            "message": "No materials indexed yet"
        }
    
    materials = marketing_vector_store.materials
    total = len(materials)
    
    # Paginate
    paginated = materials[offset:offset + limit]
    
    return {
        "materials": [m.to_dict() for m in paginated],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
