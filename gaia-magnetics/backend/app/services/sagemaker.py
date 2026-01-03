"""
SageMaker service.
Handles model training and batch prediction jobs.
"""

import boto3
import time
from datetime import datetime
from typing import Dict, Any, Optional

from ..config import settings


def get_sagemaker_client():
    """Create SageMaker client with configured credentials."""
    return boto3.client(
        "sagemaker",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region
    )


def get_xgboost_image_uri() -> str:
    """
    Get the XGBoost container image URI for the configured region.
    
    Returns:
        ECR image URI for XGBoost
    """
    # XGBoost container registry mapping
    region_map = {
        "us-east-1": "683313688378",
        "us-east-2": "257758044811",
        "us-west-1": "746614075791",
        "us-west-2": "246618743249",
        "eu-west-1": "685385470294",
        "eu-west-2": "644912444149",
        "eu-central-1": "492215442770",
        "ap-southeast-1": "121021644041",
        "ap-southeast-2": "783357654285",
        "ap-northeast-1": "354813040037",
        "ap-northeast-2": "366743142698",
        "ap-south-1": "720646828776",
        "sa-east-1": "855470959533",
        "af-south-1": "455444449433",
    }
    
    account = region_map.get(settings.aws_region, "683313688378")  # Default to us-east-1
    
    return f"{account}.dkr.ecr.{settings.aws_region}.amazonaws.com/sagemaker-xgboost:1.5-1"


def start_training_job(
    job_id: str,
    train_s3_uri: str,
    output_s3_uri: str
) -> str:
    """
    Start XGBoost training job on SageMaker.
    
    Args:
        job_id: Gaia job identifier
        train_s3_uri: S3 URI to training CSV
        output_s3_uri: S3 URI for model output
    
    Returns:
        SageMaker training job name
    """
    sagemaker = get_sagemaker_client()
    
    # Generate unique training job name
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    training_job_name = f"gaia-train-{job_id.replace('gaia-', '')}-{timestamp}"
    
    # XGBoost hyperparameters for regression
    hyperparameters = {
        "objective": "reg:squarederror",
        "num_round": "100",
        "max_depth": "6",
        "eta": "0.3",
        "subsample": "0.8",
        "colsample_bytree": "0.8",
        "eval_metric": "rmse"
    }
    
    # Training job configuration
    training_params = {
        "TrainingJobName": training_job_name,
        "HyperParameters": hyperparameters,
        "AlgorithmSpecification": {
            "TrainingImage": get_xgboost_image_uri(),
            "TrainingInputMode": "File"
        },
        "RoleArn": settings.sagemaker_role_arn,
        "InputDataConfig": [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": train_s3_uri,
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "ContentType": "text/csv"
            }
        ],
        "OutputDataConfig": {
            "S3OutputPath": output_s3_uri
        },
        "ResourceConfig": {
            "InstanceType": settings.sagemaker_instance_type,
            "InstanceCount": 1,
            "VolumeSizeInGB": 10
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 3600  # 1 hour max
        }
    }
    
    # Start training job
    sagemaker.create_training_job(**training_params)
    
    return training_job_name


def wait_for_training(training_job_name: str, poll_interval: int = 30) -> Dict[str, Any]:
    """
    Wait for training job to complete.
    
    Args:
        training_job_name: SageMaker training job name
        poll_interval: Seconds between status checks
    
    Returns:
        Training job description
    
    Raises:
        Exception: If training fails
    """
    sagemaker = get_sagemaker_client()
    
    while True:
        response = sagemaker.describe_training_job(TrainingJobName=training_job_name)
        status = response["TrainingJobStatus"]
        
        if status == "Completed":
            return response
        elif status == "Failed":
            error_msg = response.get("FailureReason", "Unknown error")
            raise Exception(f"Training job failed: {error_msg}")
        elif status == "Stopped":
            raise Exception("Training job was stopped")
        
        # Still in progress
        time.sleep(poll_interval)


def create_model(job_id: str, model_artifact_uri: str) -> str:
    """
    Create SageMaker model from trained artifact.
    
    Args:
        job_id: Gaia job identifier
        model_artifact_uri: S3 URI to model.tar.gz
    
    Returns:
        SageMaker model name
    """
    sagemaker = get_sagemaker_client()
    
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    model_name = f"gaia-model-{job_id.replace('gaia-', '')}-{timestamp}"
    
    sagemaker.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": get_xgboost_image_uri(),
            "ModelDataUrl": model_artifact_uri
        },
        ExecutionRoleArn=settings.sagemaker_role_arn
    )
    
    return model_name


def start_batch_transform(
    job_id: str,
    model_name: str,
    input_s3_uri: str,
    output_s3_uri: str
) -> str:
    """
    Start batch transform job for predictions.
    
    Args:
        job_id: Gaia job identifier
        model_name: SageMaker model name
        input_s3_uri: S3 URI to prediction input CSV
        output_s3_uri: S3 URI for prediction output
    
    Returns:
        Transform job name
    """
    sagemaker = get_sagemaker_client()
    
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    transform_job_name = f"gaia-transform-{job_id.replace('gaia-', '')}-{timestamp}"
    
    transform_params = {
        "TransformJobName": transform_job_name,
        "ModelName": model_name,
        "TransformInput": {
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": input_s3_uri
                }
            },
            "ContentType": "text/csv",
            "SplitType": "Line"
        },
        "TransformOutput": {
            "S3OutputPath": output_s3_uri,
            "AssembleWith": "Line"
        },
        "TransformResources": {
            "InstanceType": settings.sagemaker_instance_type,
            "InstanceCount": 1
        }
    }
    
    sagemaker.create_transform_job(**transform_params)
    
    return transform_job_name


def wait_for_transform(transform_job_name: str, poll_interval: int = 30) -> Dict[str, Any]:
    """
    Wait for transform job to complete.
    
    Args:
        transform_job_name: SageMaker transform job name
        poll_interval: Seconds between status checks
    
    Returns:
        Transform job description
    
    Raises:
        Exception: If transform fails
    """
    sagemaker = get_sagemaker_client()
    
    while True:
        response = sagemaker.describe_transform_job(TransformJobName=transform_job_name)
        status = response["TransformJobStatus"]
        
        if status == "Completed":
            return response
        elif status == "Failed":
            error_msg = response.get("FailureReason", "Unknown error")
            raise Exception(f"Transform job failed: {error_msg}")
        elif status == "Stopped":
            raise Exception("Transform job was stopped")
        
        # Still in progress
        time.sleep(poll_interval)


def cleanup_model(model_name: str) -> None:
    """
    Delete SageMaker model after use.
    
    Args:
        model_name: SageMaker model name to delete
    """
    try:
        sagemaker = get_sagemaker_client()
        sagemaker.delete_model(ModelName=model_name)
    except Exception:
        pass  # Ignore cleanup errors


def get_model_artifact_uri(training_job_name: str) -> str:
    """
    Get model artifact S3 URI from completed training job.
    
    Args:
        training_job_name: Completed training job name
    
    Returns:
        S3 URI to model.tar.gz
    """
    sagemaker = get_sagemaker_client()
    
    response = sagemaker.describe_training_job(TrainingJobName=training_job_name)
    
    return response["ModelArtifacts"]["S3ModelArtifacts"]
