"""
Configuration management for Gaia Geophysics backend.
Loads and validates environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://gaia:gaia_password@db:5432/gaia"
    
    # AWS Credentials
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    
    # S3
    s3_bucket: str = "gaia-geophysics"
    
    # SageMaker
    sagemaker_role_arn: str = ""
    sagemaker_instance_type: str = "ml.c4.8xlarge"
    
    # Application
    debug: bool = False
    temp_dir: str = "/tmp/gaia"
    domain: str = "gaia-magnetics.geodev.africa"
    
    # Job settings
    poll_interval_seconds: int = 30
    min_data_points: int = 3
    default_station_spacing: float = 10.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


def ensure_temp_dir():
    """Ensure temporary directory exists."""
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)


def get_s3_uri(job_id: str, filename: str) -> str:
    """Generate S3 URI for a job file."""
    return f"s3://{settings.s3_bucket}/jobs/{job_id}/{filename}"


def get_s3_prefix(job_id: str) -> str:
    """Generate S3 prefix for a job."""
    return f"jobs/{job_id}/"


def get_job_temp_path(job_id: str) -> Path:
    """Get temporary directory path for a job."""
    path = Path(settings.temp_dir) / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path
