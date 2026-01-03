# Gaia Geophysics

Automated geophysical survey prediction platform. Upload sparse reconnaissance data, get predictions for the entire survey area.

## Overview

Gaia uses machine learning (AWS SageMaker) to predict geophysical values at unmeasured locations based on sparse survey data. Currently supports magnetic surveys with plans to expand to gravity, IP, VES, and 2D methods.

## Architecture

```
Frontend (React) → Nginx → Backend (FastAPI) → SageMaker + S3 + PostgreSQL
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- AWS account with SageMaker access
- Domain pointed to server (gaia-magnetics.geodev.africa)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gaia.git
cd gaia
```

2. Copy environment template and fill in values:
```bash
cp .env.example .env
# Edit .env with your AWS credentials and settings
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the app at https://gaia-magnetics.geodev.africa

## Project Structure

```
gaia/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI entry point
│       ├── config.py         # Environment config
│       ├── database.py       # PostgreSQL connection
│       ├── models.py         # ORM models
│       ├── schemas.py        # Request/response schemas
│       ├── routes/           # API endpoints
│       ├── services/         # Business logic
│       └── worker/           # Background processing
├── frontend/
│   └── src/
│       ├── components/       # React components
│       └── pages/            # Page components
├── nginx/
│   └── nginx.conf           # Reverse proxy config
├── docker-compose.yml
├── init.sql                 # Database schema
└── .env.example             # Environment template
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/jobs | Submit new prediction job |
| GET | /api/jobs | List all jobs |
| GET | /api/jobs/{id} | Get job status |
| GET | /api/jobs/{id}/result | Download result CSV |
| DELETE | /api/jobs/{id} | Delete job |
| GET | /api/health | Health check |

## Data Flow

1. User uploads CSV with sparse measurements
2. Backend computes geometry and splits train/predict data
3. Data uploaded to S3
4. SageMaker trains model on measured points
5. Model predicts values at target locations
6. Results merged and returned to user

## License

Proprietary - All rights reserved
