"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ============== Job Schemas ==============

class JobCreateRequest(BaseModel):
    """Request body for creating a new job (excluding file)."""
    scenario: Literal["sparse", "explicit"] = Field(
        description="Sparse: generate prediction stations. Explicit: use existing geometry."
    )
    x_column: str = Field(description="CSV column name for X/Easting coordinate")
    y_column: str = Field(description="CSV column name for Y/Northing coordinate")
    value_column: str = Field(description="CSV column name for measured value (e.g., magnetic)")
    station_spacing: Optional[float] = Field(
        default=None,
        description="Distance between prediction stations (required for sparse scenario)"
    )
    coordinate_system: Literal["projected", "geographic"] = Field(
        default="projected",
        description="Projected (meters) or Geographic (lat/lon)"
    )


class JobResponse(BaseModel):
    """Response for a single job."""
    id: str
    scenario: str
    x_column: str
    y_column: str
    value_column: str
    station_spacing: Optional[float]
    coordinate_system: str
    status: str
    error_message: Optional[str]
    input_rows: Optional[int]
    train_rows: Optional[int]
    predict_rows: Optional[int]
    output_rows: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response for list of jobs."""
    jobs: List[JobResponse]
    total: int


class JobStatusResponse(BaseModel):
    """Minimal response for status polling."""
    id: str
    status: str
    error_message: Optional[str]
    progress: Optional[str] = Field(
        default=None,
        description="Human-readable progress indicator"
    )


# ============== Result Schemas ==============

class ResultRow(BaseModel):
    """Single row of result data."""
    distance: float
    x: float
    y: float
    value: float
    source: Literal["measured", "predicted"]
    uncertainty: Optional[float] = None


class ResultResponse(BaseModel):
    """Response for job results as JSON."""
    job_id: str
    columns: List[str]
    data: List[ResultRow]
    total_rows: int
    measured_count: int
    predicted_count: int


# ============== Health Check Schemas ==============

class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str
    database: bool
    s3: bool
    timestamp: datetime


# ============== Error Schemas ==============

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
