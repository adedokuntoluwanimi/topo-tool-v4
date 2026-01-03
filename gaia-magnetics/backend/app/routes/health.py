"""
Health check endpoint.
"""

from fastapi import APIRouter
from datetime import datetime

from ..schemas import HealthResponse
from ..database import check_database_connection
from ..services.s3 import check_s3_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Check health of all service dependencies.
    Returns status of database and S3 connections.
    """
    db_ok = check_database_connection()
    s3_ok = check_s3_connection()
    
    overall_status = "healthy" if (db_ok and s3_ok) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        database=db_ok,
        s3=s3_ok,
        timestamp=datetime.utcnow()
    )
