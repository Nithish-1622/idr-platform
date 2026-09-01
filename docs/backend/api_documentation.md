# IDR Backend API Overview

All API endpoints are versioned under the `/api/v1/` prefix and return JSON.

## Key API Endpoints

### 1. Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/register/` - Register backend admin/engineer/analyst user.
- `POST /api/v1/auth/token/` - Obtain JWT access and refresh token.
- `POST /api/v1/auth/token/refresh/` - Refresh access token.
- `GET  /api/v1/auth/me/` - Retrieve current user profile.

### 2. Device Management (`/api/v1/devices/`)
- `POST /api/v1/devices/register/` - Register mobile device metadata & capabilities.
- `GET  /api/v1/devices/` - List registered devices (Engineer access).
- `GET  /api/v1/devices/{id}/` - Get device details.
- `POST /api/v1/devices/{id}/heartbeat/` - Submit device heartbeat & active model/map versions.

### 3. Model Management (`/api/v1/models/`)
- `GET  /api/v1/models/` - List ML models and versions.
- `GET  /api/v1/models/latest/` - Fetch latest active ONNX model for mobile deployment.
- `POST /api/v1/models/{version_id}/approve/` - Approve model version.
- `POST /api/v1/models/{version_id}/publish/` - Atomically activate and publish model version.

### 4. Map Packages (`/api/v1/maps/`)
- `GET  /api/v1/maps/` - List active map packages.
- `GET  /api/v1/maps/lookup/?lat=...&lng=...` - Spatial query for map package at coordinates.

### 5. Telemetry Ingestion (`/api/v1/telemetry/`)
- `POST /api/v1/telemetry/batch/` - Idempotent batch upload of summarized navigation states.
- `GET  /api/v1/telemetry/sessions/` - Query telemetry sessions (Analyst access).

### 6. Configurations & Sync (`/api/v1/config/`)
- `GET  /api/v1/config/` - Retrieve system configuration flags.
- `GET  /api/v1/config/sync/` - Device synchronization check.

### 7. OTA Updates (`/api/v1/ota/`)
- `POST /api/v1/ota/check/` - Query available model/map updates matching mobile compatibility rules.

### 8. Analytics (`/api/v1/analytics/`)
- `GET  /api/v1/analytics/summary/` - Aggregated system telemetry and device stats.
- `GET  /api/v1/analytics/model-performance/` - Model positioning confidence analytics.
