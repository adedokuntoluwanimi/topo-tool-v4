"""
Background worker for job processing.
"""

from .tasks import process_job

__all__ = ["process_job"]
