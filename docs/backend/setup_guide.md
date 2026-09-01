# IDR Main Backend Setup Guide

## Quick Start via Docker Compose (Recommended)

1. Ensure Docker Desktop and Docker Compose are installed.
2. From the repository root, start the complete backend infrastructure:
   ```bash
   docker compose -f infrastructure/docker-compose.yml up --build
   ```
3. Access the services:
   - Django API: `http://localhost:8000/api/v1/`
   - Health Check: `http://localhost:8000/health/ready`
   - OpenAPI Swagger UI: `http://localhost:8000/api/docs/`
   - Django Admin: `http://localhost:8000/admin/`

---

## Local Development Setup (Host Python)

1. Create and activate a Python 3.12+ virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set environment variable for local test SQLite fallback:
   ```bash
   export USE_SQLITE_TEST=True  # On Windows PowerShell: $env:USE_SQLITE_TEST="True"
   ```
4. Run migrations and tests:
   ```bash
   cd backend
   python manage.py migrate
   pytest
   ```
