"""
SQLAlchemy ORM models for Gaia Geophysics.
"""

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class Job(Base):
    """
    Represents a geophysics prediction job.
    
    Status flow:
    pending → processing → training → predicting → merging → complete
    pending → failed (at any step)
    """
    
    __tablename__ = "jobs"
    
    # Primary key: gaia-{uuid}
    id = Column(String(50), primary_key=True)
    
    # Configuration from user
    scenario = Column(String(20), nullable=False)  # "sparse" or "explicit"
    x_column = Column(String(100), nullable=False)
    y_column = Column(String(100), nullable=False)
    value_column = Column(String(100), nullable=False)
    station_spacing = Column(Float, nullable=True)  # Required for sparse
    coordinate_system = Column(String(20), default="projected")  # "projected" or "geographic"
    
    # Status tracking
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    
    # Row counts for metadata
    input_rows = Column(Integer, nullable=True)
    train_rows = Column(Integer, nullable=True)
    predict_rows = Column(Integer, nullable=True)
    output_rows = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # S3 location
    s3_prefix = Column(String(255), nullable=True)
    
    # Relationship to logs
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job {self.id} status={self.status}>"
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in ("complete", "failed")
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently processing."""
        return self.status in ("processing", "training", "predicting", "merging")


class JobLog(Base):
    """
    Log entries for job processing stages.
    Useful for debugging and monitoring.
    """
    
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to job
    job = relationship("Job", back_populates="logs")
    
    def __repr__(self):
        return f"<JobLog {self.job_id} stage={self.stage}>"
