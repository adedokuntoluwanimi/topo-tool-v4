"""
S3 operations service.
Handles upload, download, and management of job artifacts.
"""

import boto3
import pandas as pd
from io import StringIO, BytesIO
from typing import Optional

from ..config import settings


def get_s3_client():
    """Create S3 client with configured credentials."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region
    )


def check_s3_connection() -> bool:
    """
    Check if S3 bucket is accessible.
    Used by health check endpoint.
    """
    try:
        s3 = get_s3_client()
        s3.head_bucket(Bucket=settings.s3_bucket)
        return True
    except Exception:
        return False


def upload_csv(job_id: str, filename: str, df: pd.DataFrame, header: bool = True) -> str:
    """
    Upload DataFrame as CSV to S3.
    
    Args:
        job_id: Job identifier
        filename: Target filename (e.g., "input/train.csv")
        df: DataFrame to upload
        header: Whether to include header row (False for SageMaker files)
    
    Returns:
        S3 URI of uploaded file
    """
    s3 = get_s3_client()
    
    # Convert DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=header)
    
    # Construct S3 key
    key = f"jobs/{job_id}/{filename}"
    
    # Upload
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv"
    )
    
    return f"s3://{settings.s3_bucket}/{key}"


def upload_raw_file(job_id: str, file_path: str) -> str:
    """
    Upload raw file from local path to S3.
    
    Args:
        job_id: Job identifier
        file_path: Local file path
    
    Returns:
        S3 URI of uploaded file
    """
    s3 = get_s3_client()
    
    key = f"jobs/{job_id}/input/raw.csv"
    
    s3.upload_file(
        Filename=file_path,
        Bucket=settings.s3_bucket,
        Key=key
    )
    
    return f"s3://{settings.s3_bucket}/{key}"


def download_csv(job_id: str, filename: str) -> pd.DataFrame:
    """
    Download CSV from S3 as DataFrame.
    
    Args:
        job_id: Job identifier
        filename: Source filename (e.g., "results/result.csv")
    
    Returns:
        DataFrame with file contents
    """
    s3 = get_s3_client()
    
    key = f"jobs/{job_id}/{filename}"
    
    response = s3.get_object(Bucket=settings.s3_bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    
    return pd.read_csv(StringIO(content))


def download_file(job_id: str, filename: str) -> bytes:
    """
    Download file from S3 as bytes.
    
    Args:
        job_id: Job identifier
        filename: Source filename
    
    Returns:
        File contents as bytes
    """
    s3 = get_s3_client()
    
    key = f"jobs/{job_id}/{filename}"
    
    response = s3.get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()


def generate_presigned_url(job_id: str, filename: str, expiry: int = 3600) -> str:
    """
    Generate presigned URL for file download.
    
    Args:
        job_id: Job identifier
        filename: File to generate URL for
        expiry: URL expiry time in seconds (default 1 hour)
    
    Returns:
        Presigned URL string
    """
    s3 = get_s3_client()
    
    key = f"jobs/{job_id}/{filename}"
    
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key
        },
        ExpiresIn=expiry
    )
    
    return url


def delete_job_artifacts(job_id: str) -> None:
    """
    Delete all S3 artifacts for a job.
    
    Args:
        job_id: Job identifier
    """
    s3 = get_s3_client()
    
    prefix = f"jobs/{job_id}/"
    
    # List all objects with prefix
    response = s3.list_objects_v2(
        Bucket=settings.s3_bucket,
        Prefix=prefix
    )
    
    if "Contents" not in response:
        return
    
    # Delete each object
    objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
    
    if objects:
        s3.delete_objects(
            Bucket=settings.s3_bucket,
            Delete={"Objects": objects}
        )


def get_s3_uri(job_id: str, filename: str) -> str:
    """
    Get full S3 URI for a file.
    
    Args:
        job_id: Job identifier
        filename: Filename within job folder
    
    Returns:
        Full S3 URI
    """
    return f"s3://{settings.s3_bucket}/jobs/{job_id}/{filename}"


def get_s3_path(job_id: str, filename: str) -> str:
    """
    Get S3 key (path without bucket) for a file.
    
    Args:
        job_id: Job identifier
        filename: Filename within job folder
    
    Returns:
        S3 key
    """
    return f"jobs/{job_id}/{filename}"
