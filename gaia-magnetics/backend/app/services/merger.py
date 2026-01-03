"""
Result merger service.
Combines predictions with original measured data into final output.
"""

import pandas as pd
import numpy as np
from typing import Tuple

from .s3 import download_csv, upload_csv


def parse_sagemaker_output(job_id: str) -> pd.DataFrame:
    """
    Parse SageMaker batch transform output.
    
    SageMaker outputs predictions in a file with same name as input + ".out"
    Format is one prediction per line.
    
    Args:
        job_id: Gaia job identifier
    
    Returns:
        DataFrame with predictions
    """
    from .s3 import download_file, get_s3_client
    from ..config import settings
    
    s3 = get_s3_client()
    
    # List files in output directory to find the output file
    prefix = f"jobs/{job_id}/output/"
    response = s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=prefix)
    
    output_key = None
    for obj in response.get("Contents", []):
        if obj["Key"].endswith(".out"):
            output_key = obj["Key"]
            break
    
    if not output_key:
        raise Exception("SageMaker output file not found")
    
    # Download output file
    response = s3.get_object(Bucket=settings.s3_bucket, Key=output_key)
    content = response["Body"].read().decode("utf-8")
    
    # Parse predictions (one per line) and round to 4 decimal places
    predictions = []
    for line in content.strip().split("\n"):
        if line:
            predictions.append(round(float(line.strip()), 4))
    
    return predictions


def merge_results(job_id: str) -> int:
    """
    Merge training data with predictions into final result.
    
    Args:
        job_id: Gaia job identifier
    
    Returns:
        Total number of rows in result
    """
    # Download training data (measured points)
    train_df = download_csv(job_id, "input/train.csv")
    
    # Download prediction input (distances and coordinates)
    predict_df = download_csv(job_id, "input/predict.csv")
    
    # Parse SageMaker predictions
    predictions = parse_sagemaker_output(job_id)
    
    # Add predictions to predict_df
    predict_df["value"] = predictions
    
    # Add source column
    train_df["source"] = "measured"
    predict_df["source"] = "predicted"
    
    # For measured data, uncertainty is 0
    train_df["uncertainty"] = 0.0
    
    # For predicted data, estimate uncertainty
    # Simple approach: use distance to nearest measured point
    predict_df["uncertainty"] = calculate_uncertainty(
        train_df["distance"].values,
        predict_df["distance"].values
    )
    
    # Combine DataFrames
    result_df = pd.concat([train_df, predict_df], ignore_index=True)
    
    # Sort by distance
    result_df = result_df.sort_values("distance").reset_index(drop=True)
    
    # Round numeric columns to 4 decimal places
    result_df["distance"] = result_df["distance"].round(4)
    result_df["x"] = result_df["x"].round(4)
    result_df["y"] = result_df["y"].round(4)
    result_df["value"] = result_df["value"].round(4)
    result_df["uncertainty"] = result_df["uncertainty"].round(4)
    
    # Ensure column order
    result_df = result_df[["distance", "x", "y", "value", "source", "uncertainty"]]
    
    # Upload result
    upload_csv(job_id, "results/result.csv", result_df)
    
    return len(result_df)


def calculate_uncertainty(
    measured_distances: np.ndarray,
    predicted_distances: np.ndarray,
    base_uncertainty: float = 1.0,
    distance_factor: float = 0.1
) -> np.ndarray:
    """
    Calculate uncertainty for predicted values based on distance to nearest measurement.
    
    Simple heuristic: uncertainty increases with distance from measured points.
    
    Args:
        measured_distances: Distances of measured points
        predicted_distances: Distances of predicted points
        base_uncertainty: Minimum uncertainty value
        distance_factor: How much uncertainty increases per unit distance
    
    Returns:
        Array of uncertainty values
    """
    uncertainties = []
    
    for pred_dist in predicted_distances:
        # Find distance to nearest measured point
        min_distance = np.min(np.abs(measured_distances - pred_dist))
        
        # Calculate uncertainty
        uncertainty = base_uncertainty + (min_distance * distance_factor)
        uncertainties.append(uncertainty)
    
    return np.array(uncertainties)


def validate_merge(job_id: str) -> Tuple[bool, str]:
    """
    Validate merged results.
    
    Args:
        job_id: Gaia job identifier
    
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        result_df = download_csv(job_id, "results/result.csv")
        
        # Check required columns exist
        required_cols = ["distance", "x", "y", "value", "source", "uncertainty"]
        missing = [col for col in required_cols if col not in result_df.columns]
        if missing:
            return False, f"Missing columns: {missing}"
        
        # Check no NaN values in critical columns
        for col in ["distance", "x", "y", "value"]:
            if result_df[col].isna().any():
                return False, f"NaN values found in {col}"
        
        # Check source values are valid
        valid_sources = {"measured", "predicted"}
        if not set(result_df["source"].unique()).issubset(valid_sources):
            return False, "Invalid source values"
        
        # Check sorted by distance
        if not result_df["distance"].is_monotonic_increasing:
            return False, "Results not sorted by distance"
        
        return True, "Validation passed"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"
