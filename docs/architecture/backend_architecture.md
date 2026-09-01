# Intelligent Dead Reckoning (IDR) Main Backend Architecture

## Architectural Boundary Notice
> **CRITICAL**: The Main Backend is NEVER part of the real-time navigation loop.
> The Edge Runtime (React Native / C++ Engine) acquires IMU sensors, runs ONNX inference models, performs INS propagation, EKF/UKF sensor fusion, dead reckoning, and offline map matching **without internet or backend calls**.
> If the Main Backend server is powered off, mobile navigation continues unaffected.

---

## System Domain Modules

The Main Backend is implemented as a **Modular Monolith** in Django 5 / DRF with PostgreSQL + PostGIS, Redis, and Celery:

1. **`accounts`**: User identities, role-based authorization (`ADMIN`, `ENGINEER`, `ANALYST`, `DEVICE`), JWT token issue/refresh.
2. **`devices`**: Device registration, hardware/IMU capabilities tracking, active ONNX model version, active map version, heartbeat tracking.
3. **`datasets`**: Dataset metadata (source, version, SHA256 checksum, validation status). Raw dataset binaries stored in abstract storage.
4. **`models`**: ML Model lifecycle registry (`DRAFT` -> `VALIDATING` -> `APPROVED` -> `ACTIVE` -> `DEPRECATED` -> `REVOKED`), ONNX artifact tracking, compatibility verification.
5. **`maps`**: Map package metadata, regions, spatial bounding box lookup, download links.
6. **`telemetry`**: Batch ingestion of summarized navigation state payloads uploaded asynchronously when connectivity returns. Idempotent processing using `batch_id`.
7. **`configurations`**: Central server-driven configuration (feature flags, upload frequencies, minimum app version rules) with per-device overrides.
8. **`ota`**: Update manifests for ONNX models and map packages with checksum and app version compatibility enforcement.
9. **`analytics`**: Aggregated positioning accuracy metrics, mode distribution, device health stats.

---

## Data Model & Spatial Convention

- **Database**: PostgreSQL 16 with PostGIS extensions (`django.contrib.gis`).
- **Coordinate Reference**: WGS-84 (EPSG:4326).
- **Coordinate Order**: Latitude [-90 to +90], Longitude [-180 to +180].
