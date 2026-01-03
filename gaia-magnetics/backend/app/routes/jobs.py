"""
Job management endpoints.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json
import threading

from ..database import get_db
from ..models import Job
from ..schemas import (
    JobCreateRequest,
    JobResponse,
    JobListResponse,
    JobStatusResponse,
    ResultResponse,
    ResultRow,
    ErrorResponse
)
from ..config import settings, get_job_temp_path, ensure_temp_dir
from ..services.s3 import generate_presigned_url, download_csv
from ..worker.tasks import process_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def generate_job_id() -> str:
    """Generate unique job ID."""
    return f"gaia-{uuid.uuid4().hex[:12]}"


@router.post("", response_model=JobStatusResponse)
async def create_job(
    file: UploadFile = File(..., description="CSV file with survey data"),
    scenario: str = Form(...),
    x_column: str = Form(...),
    y_column: str = Form(...),
    value_column: str = Form(...),
    station_spacing: Optional[float] = Form(default=None),
    coordinate_system: str = Form(default="projected"),
    db: Session = Depends(get_db)
):
    """
    Submit a new prediction job.
    
    1. Validates the request
    2. Saves CSV to temp storage
    3. Creates job record
    4. Queues background processing
    5. Returns job ID immediately
    """
    # Validate scenario and spacing
    if scenario not in ("sparse", "explicit"):
        raise HTTPException(status_code=400, detail="Scenario must be 'sparse' or 'explicit'")
    
    if scenario == "sparse" and station_spacing is None:
        raise HTTPException(status_code=400, detail="station_spacing required for sparse scenario")
    
    if coordinate_system not in ("projected", "geographic"):
        raise HTTPException(status_code=400, detail="coordinate_system must be 'projected' or 'geographic'")
    
    # Validate file
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Generate job ID
    job_id = generate_job_id()
    
    # Ensure temp directory exists
    ensure_temp_dir()
    
    # Save uploaded file to temp storage
    temp_path = get_job_temp_path(job_id)
    raw_path = temp_path / "raw.csv"
    
    try:
        content = await file.read()
        with open(raw_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Validate CSV has required columns
    try:
        import pandas as pd
        df = pd.read_csv(raw_path, nrows=5)
        
        missing_cols = []
        for col in [x_column, y_column, value_column]:
            if col not in df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Columns not found in CSV: {', '.join(missing_cols)}"
            )
        
        # Count total rows
        df_full = pd.read_csv(raw_path)
        input_rows = len(df_full)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    # Create job record
    job = Job(
        id=job_id,
        scenario=scenario,
        x_column=x_column,
        y_column=y_column,
        value_column=value_column,
        station_spacing=station_spacing,
        coordinate_system=coordinate_system,
        status="pending",
        input_rows=input_rows,
        s3_prefix=f"jobs/{job_id}/"
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background processing in a thread
    thread = threading.Thread(target=process_job, args=(job_id,))
    thread.start()
    
    return JobStatusResponse(
        id=job_id,
        status="pending",
        error_message=None,
        progress="Job submitted, starting processing..."
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(db: Session = Depends(get_db)):
    """
    List all jobs, ordered by creation date (newest first).
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=len(jobs)
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get minimal status for polling.
    Lighter than full job details.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate progress message
    progress_messages = {
        "pending": "Waiting to start...",
        "processing": "Computing geometry and splitting data...",
        "training": "Training model on measured data...",
        "predicting": "Generating predictions...",
        "merging": "Combining results...",
        "complete": "Job complete!",
        "failed": "Job failed"
    }
    
    return JobStatusResponse(
        id=job.id,
        status=job.status,
        error_message=job.error_message,
        progress=progress_messages.get(job.status, job.status)
    )


@router.get("/{job_id}/result")
async def get_job_result(job_id: str, db: Session = Depends(get_db)):
    """
    Download result CSV.
    Returns presigned S3 URL or streams file directly.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job.status}")
    
    try:
        # Generate presigned URL for download
        url = generate_presigned_url(job_id, "results/result.csv")
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.get("/{job_id}/result.json", response_model=ResultResponse)
async def get_job_result_json(job_id: str, db: Session = Depends(get_db)):
    """
    Get result data as JSON for visualization.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job.status}")
    
    try:
        # Download result CSV from S3
        df = download_csv(job_id, "results/result.csv")
        
        # Convert to response format
        data = []
        for _, row in df.iterrows():
            data.append(ResultRow(
                distance=row["distance"],
                x=row["x"],
                y=row["y"],
                value=row["value"],
                source=row["source"],
                uncertainty=row.get("uncertainty")
            ))
        
        measured_count = len([d for d in data if d.source == "measured"])
        predicted_count = len([d for d in data if d.source == "predicted"])
        
        return ResultResponse(
            job_id=job_id,
            columns=list(df.columns),
            data=data,
            total_rows=len(data),
            measured_count=measured_count,
            predicted_count=predicted_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete a job and its associated data.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete S3 artifacts
    try:
        from ..services.s3 import delete_job_artifacts
        delete_job_artifacts(job_id)
    except Exception:
        pass  # Continue even if S3 cleanup fails
    
    # Delete temp files
    try:
        import shutil
        temp_path = get_job_temp_path(job_id)
        if temp_path.exists():
            shutil.rmtree(temp_path)
    except Exception:
        pass
    
    # Delete database record
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted", "job_id": job_id}
