"""
Background job processing tasks.
"""

import traceback
import pandas as pd
from datetime import datetime
from pathlib import Path

from ..config import settings, get_job_temp_path
from ..database import SessionLocal
from ..models import Job, JobLog
from ..services.geometry import split_train_predict, split_train_predict_explicit
from ..services.s3 import upload_csv, upload_raw_file, get_s3_uri
from ..services.sagemaker import (
    start_training_job,
    wait_for_training,
    create_model,
    start_batch_transform,
    wait_for_transform,
    cleanup_model,
    get_model_artifact_uri
)
from ..services.merger import merge_results


def update_job_status(job_id: str, status: str, error_message: str = None):
    """Update job status in database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if status == "processing" and not job.started_at:
                job.started_at = datetime.utcnow()
            if status in ("complete", "failed"):
                job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def update_job_counts(job_id: str, train_rows: int = None, predict_rows: int = None, output_rows: int = None):
    """Update row counts in database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            if train_rows is not None:
                job.train_rows = train_rows
            if predict_rows is not None:
                job.predict_rows = predict_rows
            if output_rows is not None:
                job.output_rows = output_rows
            db.commit()
    finally:
        db.close()


def add_job_log(job_id: str, stage: str, message: str):
    """Add log entry for job."""
    db = SessionLocal()
    try:
        log = JobLog(job_id=job_id, stage=stage, message=message)
        db.add(log)
        db.commit()
    finally:
        db.close()


def get_job_config(job_id: str) -> dict:
    """Get job configuration from database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            return {
                "scenario": job.scenario,
                "x_column": job.x_column,
                "y_column": job.y_column,
                "value_column": job.value_column,
                "station_spacing": job.station_spacing,
                "coordinate_system": job.coordinate_system
            }
        return None
    finally:
        db.close()


def process_job(job_id: str):
    """
    Main job processing function.
    Called in a background thread.
    
    Phases:
    1. processing - Compute geometry, split train/predict
    2. training - Train XGBoost model on SageMaker
    3. predicting - Run batch transform
    4. merging - Combine results
    5. complete - Done
    
    Args:
        job_id: Gaia job identifier
    """
    model_name = None
    
    try:
        # Get job configuration
        config = get_job_config(job_id)
        if not config:
            raise Exception("Job not found in database")
        
        add_job_log(job_id, "start", "Starting job processing")
        
        # ============== PHASE 1: PROCESSING ==============
        update_job_status(job_id, "processing")
        add_job_log(job_id, "processing", f"Computing geometry using {config['scenario']} scenario")
        
        # Load raw CSV from temp storage
        temp_path = get_job_temp_path(job_id)
        raw_path = temp_path / "raw.csv"
        
        if not raw_path.exists():
            raise Exception("Raw CSV file not found in temp storage")
        
        df = pd.read_csv(raw_path)
        
        # Split into train and predict based on scenario
        if config["scenario"] == "explicit":
            # Explicit: split based on empty values
            train_df, predict_df = split_train_predict_explicit(
                df=df,
                x_col=config["x_column"],
                y_col=config["y_column"],
                value_col=config["value_column"],
                coordinate_system=config["coordinate_system"]
            )
        else:
            # Sparse: generate prediction stations
            train_df, predict_df = split_train_predict(
                df=df,
                x_col=config["x_column"],
                y_col=config["y_column"],
                value_col=config["value_column"],
                station_spacing=config["station_spacing"],
                coordinate_system=config["coordinate_system"]
            )
        
        # Update row counts
        update_job_counts(
            job_id,
            train_rows=len(train_df),
            predict_rows=len(predict_df)
        )
        
        add_job_log(job_id, "processing", f"Train rows: {len(train_df)}, Predict rows: {len(predict_df)}")
        
        # Upload to S3
        # For XGBoost, training data needs to be: label, feature1, feature2, ...
        # Our case: value, distance (we use distance as the only feature)
        train_sagemaker = train_df[["value", "distance"]].copy()
        train_sagemaker.columns = ["label", "distance"]
        
        upload_csv(job_id, "input/train.csv", train_df)  # Keep original for merging
        upload_csv(job_id, "input/train_sagemaker.csv", train_sagemaker, header=False)  # For SageMaker (no header)
        upload_csv(job_id, "input/predict.csv", predict_df)
        
        # Prediction input for SageMaker: just features (distance)
        predict_sagemaker = predict_df[["distance"]].copy()
        upload_csv(job_id, "input/predict_sagemaker.csv", predict_sagemaker, header=False)  # For SageMaker (no header)
        
        # Upload raw file for backup
        upload_raw_file(job_id, str(raw_path))
        
        add_job_log(job_id, "processing", "Data uploaded to S3")
        
        # ============== PHASE 2: TRAINING ==============
        update_job_status(job_id, "training")
        add_job_log(job_id, "training", "Starting SageMaker training job")
        
        train_s3_uri = get_s3_uri(job_id, "input/train_sagemaker.csv")
        output_s3_uri = f"s3://{settings.s3_bucket}/jobs/{job_id}/model/"
        
        training_job_name = start_training_job(
            job_id=job_id,
            train_s3_uri=train_s3_uri,
            output_s3_uri=output_s3_uri
        )
        
        add_job_log(job_id, "training", f"Training job started: {training_job_name}")
        
        # Wait for training to complete
        wait_for_training(training_job_name, poll_interval=settings.poll_interval_seconds)
        
        add_job_log(job_id, "training", "Training completed")
        
        # Get model artifact location
        model_artifact_uri = get_model_artifact_uri(training_job_name)
        
        # ============== PHASE 3: PREDICTING ==============
        update_job_status(job_id, "predicting")
        add_job_log(job_id, "predicting", "Creating model and starting batch transform")
        
        # Create SageMaker model
        model_name = create_model(job_id, model_artifact_uri)
        
        # Start batch transform
        predict_s3_uri = get_s3_uri(job_id, "input/predict_sagemaker.csv")
        transform_output_uri = f"s3://{settings.s3_bucket}/jobs/{job_id}/output/"
        
        transform_job_name = start_batch_transform(
            job_id=job_id,
            model_name=model_name,
            input_s3_uri=predict_s3_uri,
            output_s3_uri=transform_output_uri
        )
        
        add_job_log(job_id, "predicting", f"Transform job started: {transform_job_name}")
        
        # Wait for transform to complete
        wait_for_transform(transform_job_name, poll_interval=settings.poll_interval_seconds)
        
        add_job_log(job_id, "predicting", "Predictions completed")
        
        # ============== PHASE 4: MERGING ==============
        update_job_status(job_id, "merging")
        add_job_log(job_id, "merging", "Merging results")
        
        output_rows = merge_results(job_id)
        update_job_counts(job_id, output_rows=output_rows)
        
        add_job_log(job_id, "merging", f"Merged {output_rows} total rows")
        
        # ============== COMPLETE ==============
        update_job_status(job_id, "complete")
        add_job_log(job_id, "complete", "Job completed successfully")
        
    except Exception as e:
        # Log the error
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        add_job_log(job_id, "error", f"{error_msg}\n{traceback_str}")
        update_job_status(job_id, "failed", error_message=error_msg)
        
    finally:
        # Cleanup SageMaker model
        if model_name:
            cleanup_model(model_name)
        
        # Optionally cleanup temp files
        try:
            import shutil
            temp_path = get_job_temp_path(job_id)
            if temp_path.exists():
                shutil.rmtree(temp_path)
        except Exception:
            pass
