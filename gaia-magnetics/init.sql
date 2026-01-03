-- Gaia Geophysics Database Schema

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(50) PRIMARY KEY,
    
    -- Configuration
    scenario VARCHAR(20) NOT NULL,
    x_column VARCHAR(100) NOT NULL,
    y_column VARCHAR(100) NOT NULL,
    value_column VARCHAR(100) NOT NULL,
    station_spacing FLOAT,
    coordinate_system VARCHAR(20) DEFAULT 'projected',
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    
    -- Metadata
    input_rows INTEGER,
    train_rows INTEGER,
    predict_rows INTEGER,
    output_rows INTEGER,
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- S3 reference
    s3_prefix VARCHAR(255)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Job logs table for debugging
CREATE TABLE IF NOT EXISTS job_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) REFERENCES jobs(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON job_logs(job_id);
