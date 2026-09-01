# SIH-2026 Intelligent Dead Reckoning (IDR) Navigation Platform

"AI-ML based Intelligent Dead Reckoning system for seamless navigation."

---

## 🚨 Critical Architectural Boundary

**THE MAIN BACKEND IS NOT THE REAL-TIME NAVIGATION ENGINE.**

The mobile runtime (React Native / C++ Engine) autonomously acquires IMU sensors, performs INS propagation, AI inference, EKF/UKF fusion, dead reckoning, and offline map matching **without requiring internet or backend API calls**.

If the Main Backend server is offline, mobile navigation functions continuously without interruption.

---

## Repository Structure

```
idr-platform/
├── ml/                         # DEV1 ownership (Data, Feature engineering, Training)
├── backend/                    # DEV2 primary workspace (Main Backend)
│   ├── config/                 # Settings, Celery, ASGI/WSGI, URLs
│   ├── apps/
│   │   ├── accounts/           # Auth, JWT, Roles & Permissions
│   │   ├── devices/            # Device registration & capability metadata
│   │   ├── datasets/           # Dataset metadata management
│   │   ├── models/             # ML Model lifecycle registry & ONNX distribution
│   │   ├── telemetry/          # Offline batched telemetry ingestion (Idempotent)
│   │   ├── maps/               # Map package metadata & spatial lookup
│   │   ├── ota/                # OTA update manifests & compatibility
│   │   ├── configurations/     # Central remote config & device sync
│   │   └── analytics/          # Backend analytics & model performance stats
│   ├── common/                 # Core middleware, exceptions, pagination, storage
│   ├── tests/                  # Pytest unit & API test suite
│   ├── manage.py
│   └── requirements.txt
├── contracts/                  # Shared Contracts
│   ├── api/                    # openapi.yaml
│   ├── model/                  # schema.json
│   ├── sensor/                 # schema.json
│   └── navigation-state/       # schema.json
├── infrastructure/
│   ├── docker-compose.yml      # PostGIS, Redis, Django, Celery
│   ├── Dockerfile
│   └── entrypoint.sh
└── docs/                       # Backend architecture, API, setup guides
```

---

## Quick Start (Docker)

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

- API Base: `http://localhost:8000/api/v1/`
- Health Ready: `http://localhost:8000/health/ready`
- OpenAPI Swagger Docs: `http://localhost:8000/api/docs/`

---

## Running Tests

```bash
cd backend
USE_SQLITE_TEST=True pytest
```
