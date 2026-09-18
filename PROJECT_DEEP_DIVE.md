# 🧭 SIH 2026: Intelligent Dead Reckoning (IDR) Platform — In-Depth System & Architecture Manual

> **Project Mission**: Deliver zero-infrastructure, offline, AI-powered vehicular navigation when satellite signals (GNSS/GPS) and cellular networks completely vanish (tunnels, urban canyons, dense forests, adverse weather). By transforming consumer smartphone Inertial Measurement Units (IMU: Accelerometer + Gyroscope) into a self-calibrating inertial navigation system, the platform ensures continuous, millimeter-to-meter accurate trajectory tracking without reliance on cloud inference or vehicle wheel-tick odometry.

---

## 📑 Table of Contents

1. [Executive Summary & Core Architectural Principle](#1-executive-summary--core-architectural-principle)
2. [High-Level Directory Breakdown](#2-high-level-directory-breakdown)
3. [Deep Dive: Machine Learning Subsystem (`ml/`)](#3-deep-dive-machine-learning-subsystem-ml)
   - 3.1 Data Ingestion & Dataset Structure
   - 3.2 Data Cleaning & Sensor-Bias Rectification (`cleaner.py`)
   - 3.3 Temporal Synchronization (`sync.py`)
   - 3.4 Rotation-Invariant Gravity Alignment (`aligner.py`)
   - 3.5 Feature Engineering & Windowing (`engineer.py`)
   - 3.6 Neural Network & Baseline Architectures (`models.py`)
   - 3.7 Training Pipeline & Generalization Protocol (`trainer.py`, `train_combined.py`)
   - 3.8 Model Optimization, Export & ONNX Runtime (`exporter.py`)
   - 3.9 Evaluation Suite & 25 Edge-Case Benchmark (`validate_model.py`)
   - 3.10 Diagnostic & Experimental Scratchpad (`scratch/`)
4. [Deep Dive: Backend Control Plane Subsystem (`backend/`)](#4-deep-dive-backend-control-plane-subsystem-backend)
   - 4.1 System Boundary & Modular Monolith Pattern
   - 4.2 Application Matrix & Core Domain Responsibilities
   - 4.3 Simulation Service & Live Telemetry APIs (`apps/simulations`)
   - 4.4 Mobile IMU Telemetry Ingestion (`/api/v1/get_imu`)
   - 4.5 Common Infrastructure, Auth, Health, & Error Handling
5. [Deep Dive: Simulation Engine Subsystem (`simulation/`)](#5-deep-dive-simulation-engine-subsystem-simulation)
   - 5.1 Scenario Definitions & Real-World Presets
   - 5.2 The Sri Eshwar College Flagship Outage Scenario
   - 5.3 Sensor Degradation, Noise, & Disturbance Modeling
   - 5.4 Kinematic & Geographic Trajectory Generation
   - 5.5 Hardware Adapters & Closed-Loop ML Integration
6. [Data Contracts, Schemas & API Specifications (`contracts/`)](#6-data-contracts-schemas--api-specifications-contracts)
7. [Infrastructure, Containerization & Deployment (`infrastructure/`)](#7-infrastructure-containerization--deployment-infrastructure)
8. [Documentation & Research Artifacts (`docs/`)](#8-documentation--research-artifacts-docs)
9. [Subsystem Interaction & End-to-End Execution Flow](#9-subsystem-interaction--end-to-end-execution-flow)
10. [Performance Metrics, Benchmarks & Key Results](#10-performance-metrics-benchmarks--key-results)

---

## 1. Executive Summary & Core Architectural Principle

### 1.1 The Navigation Dilemma
Standard satellite navigation relies on line-of-sight signal transmission from GPS/GLONASS/Galileo/BeiDou constellations. When a vehicle enters underground tunnels, multi-level basements, deep urban canyons surrounded by skyscrapers, or dense vegetation, GNSS signals suffer from:
- **Total Blackout**: No satellite lock available.
- **Multipath Interference**: Radio signals reflect off glass and concrete facades, producing phantom jumps up to hundreds of meters.
- **Latency & Map Freezes**: Real-time turn guidance stops, causing missed exits and hazards.

### 1.2 The Deep IDR Solution
Deep IDR equips vehicles with an offline dead-reckoning engine powered by a **1D-Convolutional Neural Network (1D-CNN)** running entirely on-device (smartphone or embedded edge computing unit). It samples noisy, uncalibrated consumer IMU sensors at 100 Hz, extracts rotation-invariant physical dynamics, projects inertial forces relative to gravity, and infers instantaneous forward velocity and yaw rate. These are mathematically integrated via kinematic dead reckoning equations to calculate continuous Latitude, Longitude, Heading, and Speed.

```
+-----------------------------------------------------------------------------+
|                          EDGE MOBILE / EMBEDDED RUNTIME                     |
|                                                                             |
|  [Phone IMU Sensors] ---> [Gravity / Butterworth] ---> [Feature Window]     |
|   (Accel + Gyro 100Hz)         (Projected Yaw)            (10 frames)       |
|                                                                |            |
|                                                                v            |
|  [Dead Reckoned Path] <--- [Kinematics Euler] <--- [ONNX Inference Engine]  |
|  (Lat, Lon, Heading)       (Velocity, Yaw Rate)       (deep_idr.onnx: 0.5ms)|
+-----------------------------------------------------------------------------+
                                       ^
             OTA Updates / Diagnostics | (Asynchronous / When Internet Returns)
                                       v
+-----------------------------------------------------------------------------+
|                        BACKEND CONTROL PLANE (DJANGO)                       |
|                                                                             |
|  [Device Registry]   [Model Registry & OTA]   [Batch Telemetry Ingest]      |
|  [Remote Configs]    [Simulation Presets]     [PostgreSQL / PostGIS / Redis]|
+-----------------------------------------------------------------------------+
```

### 1.3 Strict Architectural Boundary Rule
> ⚠️ **CRITICAL ARCHITECTURAL BOUNDARY**:
> **The Main Backend is NEVER part of the real-time navigation loop.**
> The edge client executes all IMU sampling, feature normalization, ONNX neural inference, coordinate integration, and map tracking **100% autonomously without network access**. The backend serves strictly as a **Control Plane, Simulation Lab, Model Distribution Hub, and Asynchronous Analytics Engine**. If the backend server is terminated, offline navigation continues uninterrupted.

---

## 2. High-Level Directory Breakdown

| Directory / File | Domain Ownership | Primary Role & Contribution |
| :--- | :--- | :--- |
| [`ml/`](file:///e:/idr-platform/ml) | Machine Learning & Data Science | Complete data pipeline: raw sensor ingestion, synchronization, rotation-invariant gravity projection, 1D-CNN model architecture, training loops, evaluation suites, and ONNX model export. |
| [`backend/`](file:///e:/idr-platform/backend) | Cloud & Server Engineering | Django REST Framework modular monolith: manages device registration, OTA model distribution, map packages, asynchronous batch telemetry ingestion, remote configuration, and Celery simulation runs. |
| [`simulation/`](file:///e:/idr-platform/simulation) | Simulation & Physics Engine | Generates synthetic and real-world driving environments, GNSS blackouts, IMU noise profiles, kinematic trajectories, and runs closed-loop validation against the ONNX model. |
| [`contracts/`](file:///e:/idr-platform/contracts) | Systems Architecture & QA | Single-source-of-truth JSON schemas and OpenAPI specifications defining model inputs/outputs, sensor formats, and navigation states. |
| [`infrastructure/`](file:///e:/idr-platform/infrastructure) | DevOps & Deployment | Multi-container Docker orchestration (`docker-compose.yml`, `Dockerfile`, `entrypoint.sh`) packaging PostgreSQL/PostGIS, Redis, Celery workers, and Django. |
| [`docs/`](file:///e:/idr-platform/docs) | Architecture & Documentation | Technical whitepapers, API guides, Postman collections, simulation manuals, and trajectory performance charts. |
| [`.env.example`](file:///e:/idr-platform/.env.example) | Configuration | Template for environment secrets, database credentials, and operational flags. |
| [`README.md`](file:///e:/idr-platform/README.md) | Project Overview | Hackathon entry document summarizing key features, benchmarks, quick-start commands, and demo scenarios. |

---

## 3. Deep Dive: Machine Learning Subsystem (`ml/`)

The `ml/` subsystem houses the core scientific innovation of Deep IDR: predicting accurate vehicle dynamics from low-cost consumer smartphone sensors without requiring specialized vehicle CAN-bus connections or fixed phone mounts.

```
ml/
├── src/
│   ├── ingestion/       # Raw dataset loaders
│   ├── cleaning/        # Gap interpolation & sensor bias corrections
│   ├── synchronization/ # Cross-correlation temporal alignment (Phone vs Vehicle)
│   ├── alignment/       # Gravity vector estimation & PCA orientation invariance
│   ├── features/        # Sliding window extraction (ACC_MAG, PROJ_YAW, DYN_ACC_MAG)
│   ├── training/        # PyTorch 1D-CNN, Baseline Random Forest, Adam / LR schedulers
│   ├── evaluation/      # ATE, drift rate, per-scenario validation routines
│   └── export/          # PyTorch -> ONNX dynamic graph conversion
├── models/
│   ├── checkpoints/     # Saved PyTorch .pth weight checkpoints
│   ├── deploy/          # Production ONNX model runtime files (deep_idr.onnx)
│   └── exports/         # Versioned model release candidates
├── data/                # Ground truth datasets (Synchronised & Unsynchronised)
├── reports/             # Test execution results (e.g. model_validation_25_cases.json)
├── scratch/             # Diagnostic math, coordinate alignment, cross-check scripts
└── validate_model.py    # 25-scenario automated physical validation engine
```

### 3.1 Data Ingestion & Dataset Structure (`ml/src/ingestion/loader.py`)
- Ingests paired time-series data: **Smartphone Sensors (S)** and **Vehicle Ground Truth (V)**.
- Handles diverse ground-truth formats collected over 450,000 driving samples across multiple vehicles and drivers (e.g. datasets `S1`, `S2`, `S3a`, `S3b`, `S3c`, `S4`, `M`, `Y1`, `Vfa01`, `Vtb01`).
- Accommodates sensor column naming variations, UTF-8/Latin-1 encodings, and missing column fallback logic.

### 3.2 Data Cleaning & Sensor-Bias Rectification (`ml/src/cleaning/cleaner.py`)
- **Resampling & Linear Interpolation**: Fills small sensor drops and standardizes irregular mobile sensor frequency to a steady **10 Hz** time-base.
- **Edge Null Management**: Implements forward/backward fills (`ffill().bfill()`) to eliminate boundary anomalies.
- **Heading-Derived Yaw Rate Reconstruction**: Raw consumer gyroscope logs often exhibit severe drift, thermal bias, or faulty scale factors. The cleaner solves this by computing the analytical time derivative of the high-accuracy GNSS Heading vector over unwrapped degrees ($[-180^\circ, +180^\circ]$ wrap handling), deriving an indisputable ground-truth target yaw rate for supervised training.

### 3.3 Temporal Synchronization (`ml/src/synchronization/sync.py`)
- Smartphones and vehicle reference loggers run on unsynchronized, independent hardware clocks.
- The synchronizer leverages **Pandas `merge_asof`** matching relative elapsed runtimes ($\Delta t$ from start of drive) within a strict configurable tolerance window (typically $\le 200\text{ ms}$).
- Validates row-to-row timestamp alignment, rejecting asynchronous noise or corrupted segments.

### 3.4 Rotation-Invariant Gravity Alignment (`ml/src/alignment/aligner.py`)
One of the most critical breakthroughs of this project is **Mounting Independence**. In real-world driving, a driver may mount their phone vertically on the dash, horizontally on a vent, resting in a cup holder, or tilted at an arbitrary 3D angle. Raw 3-axis readings ($a_x, a_y, a_z, \omega_x, \omega_y, \omega_z$) vary wildly depending on orientation. The `IMUAligner` neutralizes this variance:
1. **Gravity Vector Isolation**: Computes the unit gravity direction vector $\hat{g} = [n_x, n_y, n_z]^T$ from low-frequency accelerometer/gravity components:
   $$g_{\text{mag}} = \sqrt{g_x^2 + g_y^2 + g_z^2}, \quad \hat{g} = \frac{\vec{g}}{g_{\text{mag}}}$$
2. **Dynamic Acceleration Extraction**: Subtracts static gravity from total raw acceleration:
   $$\vec{a}_{\text{dyn}} = \vec{a}_{\text{raw}} - \vec{g}$$
3. **Horizontal Plane Projection**: Projects dynamic acceleration onto the horizontal plane perpendicular to gravity by subtracting the vertical normal component:
   $$\vec{a}_{\text{horiz}} = \vec{a}_{\text{dyn}} - (\vec{a}_{\text{dyn}} \cdot \hat{g}) \hat{g}$$
4. **Projected Yaw Rate (`PROJ_YAW`)**: Computes the scalar dot product between the 3D gyroscope vector $\vec{\omega}$ and the unit gravity normal $\hat{g}$:
   $$\text{PROJ\_YAW} = \vec{\omega} \cdot \hat{g} = \omega_x n_x + \omega_y n_y + \omega_z n_z$$
   This yields the true vehicle turning rate regardless of device pitch, roll, or inverted mounting.
5. **PCA Forward/Lateral Axis Resolution**: Uses 2-component Principal Component Analysis (PCA) on horizontal acceleration vectors to decompose forward surge and lateral sway.

### 3.5 Feature Engineering & Windowing (`ml/src/features/engineer.py`)
Extracts a compact, rotation-invariant, 3-dimensional physical feature tuple:
1. **`ACC_MAG`**: Total acceleration Euclidean norm $\sqrt{a_x^2 + a_y^2 + a_z^2}$.
2. **`PROJ_YAW`**: Gravity-aligned true vehicular yaw rotation rate.
3. **`DYN_ACC_MAG`**: Magnitude of pure vehicle acceleration after removing static gravity forces.

- **Sliding Window Processing**: Rather than predicting kinematics from an isolated snapshot, the model groups features into a rolling window of **10 consecutive timesteps** (1.0 second of physical context at 10 Hz):
  - Model Input Tensor Shape: `(Batch_Size, 10, 3)`
  - Target Prediction: Instantaneous vehicle `[Velocity (m/s), Yaw Rate (deg/s)]` at the trailing edge of the window.

### 3.6 Neural Network & Baseline Architectures (`ml/src/training/models.py`)

#### Deep IDR 1D-CNN (`DeepIDRModel`)
Designed for minimal parameter count, high inference velocity, and temporal feature extraction:
- **Input Layer**: `(B, 10, 3)` transposed to `(B, 3, 10)` for Conv1D channel convention.
- **Conv1D Block 1**: 32 filters, Kernel Size 3, Padding 1 $\rightarrow$ ReLU $\rightarrow$ MaxPool1d(2).
- **Conv1D Block 2**: 64 filters, Kernel Size 3, Padding 1 $\rightarrow$ ReLU $\rightarrow$ MaxPool1d(2).
- **Dense Flattening**: Flattened representation $\rightarrow$ Linear(flat_dim, 32) $\rightarrow$ ReLU.
- **Regression Output Head**: Linear(32, 2) $\rightarrow$ predicts `[Velocity, Yaw Rate]`.
- **Parameter Footprint**: $< 2\text{ MB}$, allowing instant mobile caching.

#### Baseline Multi-Output Random Forest (`BaselineModel`)
- Uses `MultiOutputRegressor(RandomForestRegressor(n_estimators=50, max_depth=10))` on flattened 2D vectors `(N, 30)` to benchmark linear and ensemble performance against the deep neural network.

### 3.7 Training Pipeline & Generalization Protocol (`trainer.py`, `train_combined.py`)
- **Cross-Driver Generalization Split**:
  - **Train Set**: `S1`, `S2`, `S4` (~300,000 samples).
  - **Validation Set**: `S3b`, `S3c`, `M` (~100,000 samples, unseen driver/car).
  - **Zero-Shot Test Set**: `Y1` (~50,000 samples, completely unseen city and vehicle).
- **Zero-Leakage Normalization**: Standard scaler parameters (mean and standard deviation) are strictly fitted on the training split only and serialized to `norm_params_combined.json`.
- **Loss Function & Optimization**: Mean Squared Error (MSE), Adam optimizer ($\text{lr} = 0.001$), learning rate step decay (`StepLR`), and early stopping on validation loss.

### 3.8 Model Optimization & ONNX Runtime Export (`ml/src/export/`)
- Converts trained PyTorch `.pth` weights into an optimized Open Neural Network Exchange (ONNX) file: `ml/models/deploy/deep_idr.onnx`.
- Configured with **dynamic axes** for batch size (`{'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}`), permitting flexible batched evaluation or single-frame real-time streaming ($0.51\text{ ms}$ inference time).

### 3.9 Evaluation Suite & 25 Edge-Case Benchmark (`ml/validate_model.py`)
An automated validation suite executing the ONNX model against 25 physical simulation categories:
- **Category A (Stationary)**: Flat desk, in-pocket still standing, elevated platform, high-temperature thermal bias.
- **Category B (Linear Cruising)**: Highway cruising, emergency stop, stop-and-go urban crawl, high acceleration bursts.
- **Category C (Turning & Maneuvering)**: 90-degree street turn, roundabout loop, slalom chicane, hairpin curve.
- **Category D (Sensor Hardware Noise)**: Cheap IMU white noise, heavy gyroscope drift, 45-degree roll mount, inverted dash mount.
- **Category E (GNSS Outages)**: Short 10s tunnel, extended 60s mountain tunnel, urban canyon multipath drift, total GNSS loss.
- Results are compiled to `ml/reports/model_validation_25_cases.json` with a **100% test pass rate**.

### 3.10 Diagnostic & Experimental Scratchpad (`ml/scratch/`)
Scripts used during research to solve edge problems:
- `find_shift2.py`, `find_shift3.py`: Cross-correlation shift discoverers between asynchronous smartphone and vehicle clocks.
- `export_combined_onnx.py`: Standalone combined model exporter.
- `rigorous_sanity_check.py`, `plot_sanity_check.py`: Generates visual sanity check plots comparing predicted paths vs ground truth.

---

## 4. Deep Dive: Backend Control Plane Subsystem (`backend/`)

The backend is built as a high-performance **Django 5 / Django REST Framework (DRF)** modular monolith backed by PostgreSQL with PostGIS extensions, Redis, and Celery workers.

```
backend/
├── config/                  # Project configuration
│   ├── settings.py          # PostGIS, Redis, Celery, REST framework config
│   ├── urls.py              # Root API URL routing & Swagger UI
│   ├── celery.py            # Celery worker application configuration
│   ├── asgi.py & wsgi.py    # Async and standard web server gateways
├── apps/
│   ├── accounts/            # Users, JWT token auth, Roles (ADMIN, ENGINEER, DEVICE)
│   ├── devices/             # Device registration, hardware capabilities, heartbeats
│   ├── datasets/            # Dataset catalog, versioning, SHA256 integrity checks
│   ├── models/              # ML Model lifecycle registry (DRAFT -> ACTIVE -> DEPRECATED)
│   ├── maps/                # Offline vector map packages, spatial bounding box lookup
│   ├── telemetry/           # Idempotent batch telemetry ingestion with batch_id
│   ├── configurations/      # Remote dynamic configuration & per-device overrides
│   ├── ota/                 # Over-The-Air update manifests for models & maps
│   ├── analytics/           # Drift statistics, positioning accuracy rollups
│   └── simulations/         # Simulation execution, Celery tasks, preview frames, mobile API
├── common/                  # Core middleware, exceptions, pagination, health checks
├── tests/                   # Pytest automated test suite
├── manage.py
└── requirements.txt
```

### 4.1 System Boundary & Modular Monolith Pattern
The backend is intentionally partitioned into domain modules with explicit boundaries. Each application encapsulates its own models, serializers, views, services, and migrations.

### 4.2 Application Matrix & Core Domain Responsibilities

#### 1. `apps.accounts`
- Manages user accounts and JWT authentication (`access_token`, `refresh_token`).
- Enforces role-based permissions: `ADMIN`, `ENGINEER`, `ANALYST`, and `DEVICE`.

#### 2. `apps.devices`
- Handles registration of mobile smartphones and embedded edge hardware.
- Tracks device hardware specs: IMU sensor vendor, gyroscope noise density, OS version, active ONNX model version, active map version, and periodic heartbeats.

#### 3. `apps.datasets`
- Catalog of all training and validation datasets.
- Tracks dataset storage URIs, row counts, sensor channels, SHA-256 checksums, and validation status (`PENDING`, `VALIDATED`, `REJECTED`).

#### 4. `apps.models`
- Tracks the formal lifecycle of ML models: `DRAFT` $\rightarrow$ `VALIDATING` $\rightarrow$ `APPROVED` $\rightarrow$ `ACTIVE` $\rightarrow$ `DEPRECATED` $\rightarrow$ `REVOKED`.
- Holds ONNX artifact file metadata, input/output tensors, inference latency benchmarks, and compatibility requirements.

#### 5. `apps.maps`
- Manages offline map packages partitioned by geographical regions.
- Uses PostGIS spatial bounding boxes (`django.contrib.gis.db.models.PolygonField`) to allow client devices to query which offline map tiles are needed for their current route.

#### 6. `apps.telemetry`
- Ingests aggregated dead-reckoning diagnostic packets uploaded by mobile devices when cellular connectivity is restored.
- **Idempotency**: Every telemetry payload includes a unique `batch_id`. If a device retries an upload due to an unstable network, the backend ignores duplicates.

#### 7. `apps.configurations`
- Centralized remote configuration server.
- Supplies mobile clients with dynamic operational parameters: sensor sampling frequencies, telemetry upload intervals, minimum required app versions, and feature flags without requiring app store updates.

#### 8. `apps.ota`
- Distributes Over-The-Air update manifests for both ML ONNX models and map packages.
- Enforces cryptographic hash validation (SHA-256) and semantic version constraints.

#### 9. `apps.analytics`
- Aggregates fleet-wide positioning metrics: average drift rate percentages, outage duration distributions, and model performance comparisons across diverse phone manufacturers.

#### 10. `apps.simulations`
- Bridges the backend with the physical simulation engine (`simulation/`).
- Allows engineers and frontend dashboards to trigger, parameterize, inspect, and replay simulated driving routes.
- Supports both **synchronous execution** (for quick interactive previews) and **asynchronous Celery worker execution** (for heavy Monte-Carlo simulation batches).

### 4.3 Simulation Service & Live Telemetry APIs (`apps/simulations`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/simulations/presets` | Returns all 17 pre-configured simulation scenarios with duration, outage window, and description. |
| `GET` | `/api/v1/simulations/` | Lists past simulation execution runs with status and drift metrics. |
| `POST` | `/api/v1/simulations/` | Creates a new simulation run for a specific preset or custom parameter set. |
| `POST` | `/api/v1/simulations/{id}/trigger` | Triggers execution (`?sync=true` for immediate result or async Celery dispatch). |
| `GET` | `/api/v1/simulations/preview` | Generates a time-series preview stream of IMU readings, GNSS states, and calculated navigation states for frontend map animations. |

### 4.4 Mobile IMU Telemetry Ingestion (`/api/v1/get_imu`)
Exposes a unified high-speed endpoint (`MobileGetIMUView` at `/api/v1/get_imu`):
- Accepts either a single IMU+GNSS frame or a batched `time_series` array.
- Evaluates GNSS lock status:
  - If GNSS is `LOCKED` $\rightarrow$ returns `GNSS_INS` mode (Confidence: `0.98`, Drift: `0.0m`).
  - If GNSS is `UNAVAILABLE` $\rightarrow$ engages `DEAD_RECKONING` mode (Confidence: `0.72`, Drift: estimated accumulation).
- Emits standardized navigation state responses consumable by frontend mobile applications.

### 4.5 Common Infrastructure, Health & OpenAPI
- **Health Probes**: `/health/live` (liveness check) and `/health/ready` (readiness check validating PostgreSQL and Redis connectivity).
- **Interactive API Documentation**: Swagger UI at `/api/docs/` and Redoc at `/api/redoc/` generated via `drf-spectacular`.

---

## 5. Deep Dive: Simulation Engine Subsystem (`simulation/`)

The simulation engine is an autonomous physics modeling framework that generates ground-truth vehicular kinematics, synthesizes corrupted sensor streams (IMU and GNSS), and validates dead-reckoning algorithms in controlled, repeatable environments.

```
simulation/
├── scenario/         # Scenario schemas, preset library, Sri Eshwar route
├── disturbances/     # Noise injection: GNSS outages, multipath, gyro drift
├── sensors/          # Synthetic IMU & GNSS sensor simulators
├── trajectory/       # 3DOF/6DOF kinematic generators & coordinate converters
├── adapters/         # Integration adapters (ReferenceONNXIDRAdapter)
├── runner/           # SimulationEngine orchestration loop
├── evaluation/       # Absolute Trajectory Error (ATE) & Drift calculation
└── exporters/        # Export trajectories to CSV, JSON, GeoJSON
```

### 5.1 Scenario Definitions & Real-World Presets (`simulation/scenario/`)
- Configured using Pydantic/dataclass schemas (`schema.py`):
  - `SimulationScenario`: Duration, timestep, random seed, initial position/velocity/heading.
  - `MovementMode`: `CONSTANT_VELOCITY`, `ACCELERATING`, `CIRCULAR_TURN`, `SLALOM`, `WAYPOINT_ROUTE`.
  - `IMUConfig`: Accelerometer noise, bias, gyroscope random walk, thermal drift.
  - `GNSSConfig`: Output frequency (1 Hz), position noise, and scheduled outages (`start_seconds`, `end_seconds`).
- **17 Built-in Presets** (`presets.py`): Includes highway cruising, multi-lane urban roads, mountain tunnels, circular roundabouts, and parking basements.

### 5.2 The Sri Eshwar College Flagship Outage Scenario (`sri_eshwar_outage.py`)
Created as the centerpiece live demonstration for SIH 2026:
- **Location**: Sri Eshwar College campus towards Kinathukadavu (Coimbatore, Tamil Nadu; Coordinates: $10.8286^\circ\text{ N}, 77.0605^\circ\text{ E}$).
- **Trajectory**: 135 accurate GPS road waypoints spanning 360 seconds of realistic road travel.
- **The Outage Event**: At $t = 144.0\text{ s}$ (2 minutes 24 seconds into the drive), GNSS satellites and cellular connections are completely severed for **56 continuous seconds** (until $t = 200.0\text{ s}$).
- **The Test**: Evaluates whether the Deep IDR ONNX model seamlessly takes over dead reckoning during the 56-second blackout, continuing to output smooth, road-aligned coordinates without wandering off the route.

### 5.3 Sensor Degradation, Noise & Disturbance Modeling (`simulation/disturbances/`, `sensors/`)
- **IMU Modeling**: Simulates real MEMS accelerometer and gyroscope imperfections:
  $$\vec{a}_{\text{measured}} = \vec{a}_{\text{true}} + \vec{g} + \vec{b}_{\text{acc}} + \mathcal{N}(0, \sigma_{\text{acc}}^2)$$
  $$\vec{\omega}_{\text{measured}} = \vec{\omega}_{\text{true}} + \vec{b}_{\text{gyro}} + \mathcal{N}(0, \sigma_{\text{gyro}}^2)$$
- **GNSS Outage Generators**: Simulates complete signal attenuation, satellite dropouts, and gradual multipath drift where reported positions wander laterally before loss of lock.

### 5.4 Kinematic & Geographic Trajectory Generation (`simulation/trajectory/`)
- Converts vehicle motion across multiple coordinate frames:
  - **Body Frame**: Longitudinal surge, lateral sway, yaw angular velocity.
  - **ENU (East-North-Up)**: Local Cartesian coordinates in meters.
  - **ECEF (Earth-Centered, Earth-Fixed)**: 3D global Cartesian coordinates.
  - **WGS-84 (World Geodetic System 1984)**: Geodetic Latitude, Longitude, Altitude using accurate Haversine and Equirectangular projection equations.

### 5.5 Hardware Adapters & Closed-Loop ML Integration (`simulation/adapters/`)
- Provides a clean abstraction layer: `BaseIDRAdapter`.
- **`ReferenceONNXIDRAdapter`**:
  - Consumes the simulated 100 Hz IMU sensor records.
  - Feeds sliding windows into `ml/models/deploy/deep_idr.onnx`.
  - Obtains predicted forward velocity $v$ and yaw rate $\dot{\psi}$.
  - Integrates heading: $\psi_k = \psi_{k-1} + \dot{\psi}_k \cdot \Delta t$.
  - Integrates position: $x_k = x_{k-1} + v_k \cos(\psi_k) \Delta t$, $y_k = y_{k-1} + v_k \sin(\psi_k) \Delta t$.
  - Enables direct comparison of AI-estimated trajectory versus the mathematical ground truth.

---

## 6. Data Contracts, Schemas & API Specifications (`contracts/`)

To prevent divergence between ML data engineers, backend developers, and mobile frontend developers, all data contracts are defined in standardized machine-readable formats under `contracts/`:

```
contracts/
├── api/
│   └── openapi.yaml            # OpenAPI 3.0 REST API Specification
├── model/
│   ├── schema.json             # Input/Output tensor shapes and datatypes
│   ├── preprocessing.json      # Standardization scaler formulas & parameters
│   ├── deep-idr-model.json     # Metadata: version, author, checksum, latency
│   └── README.md
├── sensor/
│   └── schema.json             # JSON schema for raw Accelerometer & Gyroscope records
└── navigation-state/
    └── schema.json             # JSON schema for estimated vehicle navigation state
```

### Key Contract Definitions
- **`model/schema.json`**: Mandates input tensor `float32 [Batch, 10, 3]` and output tensor `float32 [Batch, 2]`.
- **`sensor/schema.json`**: Mandates timestamp in milliseconds, 3-axis accelerometer values in $\text{m/s}^2$, and 3-axis gyroscope values in $\text{rad/s}$.
- **`navigation-state/schema.json`**: Mandates output fields: `latitude`, `longitude`, `speed_kmh`, `heading_deg`, `confidence_score` ($[0.0, 1.0]$), `drift_estimate_m`, and `navigation_mode` (`GNSS_INS` vs `DEAD_RECKONING`).

---

## 7. Infrastructure, Containerization & Deployment (`infrastructure/`)

The infrastructure folder provides a containerized development and production setup:

```
infrastructure/
├── Dockerfile          # Multi-stage Python 3.11 container definition with GDAL/PostGIS
├── docker-compose.yml  # Multi-service stack (Django, PostgreSQL+PostGIS, Redis, Celery)
└── entrypoint.sh       # Container bootstrap: migrations, static collection, server startup
```

### 7.1 Multi-Service Topology
1. **`db` (PostgreSQL 16 + PostGIS 3.4)**: Stores relational data, spatial polygons for maps, and device telemetry.
2. **`redis` (Redis 7 Alpine)**: In-memory cache and task message broker for asynchronous jobs.
3. **`backend` (Django DRF / Gunicorn)**: Exposes the HTTP REST API, processes simulation requests, and serves Swagger documentation.
4. **`celery_worker`**: Asynchronously executes compute-heavy simulation jobs and batch telemetry analyses.

---

## 8. Documentation & Research Artifacts (`docs/`)

The `docs/` folder contains comprehensive documentation and empirical evidence supporting the platform's validity:

- [`docs/ml/model_architecture.md`](file:///e:/idr-platform/docs/ml/model_architecture.md): Full theoretical specification of the 1D-CNN, Butterworth filtering, and training protocol.
- [`docs/ml/dataset_report.md`](file:///e:/idr-platform/docs/ml/dataset_report.md): Statistical analysis of 450,000+ training frames across Indian urban driving conditions.
- [`docs/simulation_endpoints.md`](file:///e:/idr-platform/docs/simulation_endpoints.md) & [`docs/simulation/SIMULATION_BACKEND_DEVELOPER_GUIDE.md`](file:///e:/idr-platform/docs/simulation/SIMULATION_BACKEND_DEVELOPER_GUIDE.md): Complete guide for frontend and mobile engineers connecting to simulation endpoints.
- **Empirical Visualizations**: High-resolution PNG trajectory comparisons (e.g., `trajectory_S1.png`, `trajectory_Y1.png`, `trajectory_M.png`, `rigorous_sanity_Vtb03.png`) showing Ground Truth vs Dead Reckoned paths under severe GNSS outage conditions.

---

## 9. Subsystem Interaction & End-to-End Execution Flow

The sequence below illustrates how all folders collaborate during the life of a navigation session:

```
+-----------+            +--------------+            +----------------+            +---------------+
| Edge App  |            |   Backend    |            |   ML Engine    |            |  Simulation   |
|  (Mobile) |            |  (backend/)  |            |     (ml/)      |            | (simulation/) |
+-----+-----+            +------+-------+            +-------+--------+            +-------+-------+
      |                         |                            |                             |
      | 1. Register Device      |                            |                             |
      |------------------------>|                            |                             |
      | 2. Sync OTA Model       |                            |                             |
      |<------------------------| (Delivers deep_idr.onnx)   |                             |
      |                         |                            |                             |
      | 3. Normal GNSS Driving  |                            |                             |
      |    (Satellite Locked)   |                            |                             |
      |                         |                            |                             |
      | 4. GNSS OUTAGE OCCURS!  |                            |                             |
      |    (Tunnel / Canyon)    |                            |                             |
      |                         |                            |                             |
      | 5. Process IMU at 100Hz |                            |                             |
      |----------------------------------------------------->| (Extract 10-step window)    |
      | 6. Predicted Velocity & Yaw                          |                             |
      |<-----------------------------------------------------| (Inference in 0.51 ms)      |
      |                         |                            |                             |
      | 7. Euler Dead Reckoning |                            |                             |
      |    (Updates Map Path)   |                            |                             |
      |                         |                            |                             |
      | 8. Signal Restored      |                            |                             |
      |    Batch Telemetry      |                            |                             |
      |------------------------>| (Idempotent batch upload)  |                             |
      |                         |                            |                             |
      |                         | 9. Run Offline Benchmark   |                             |
      |                         |--------------------------------------------------------->|
      |                         | 10. Trajectory Accuracy Evaluation Report                |
      |                         |<---------------------------------------------------------|
```

---

## 10. Performance Metrics, Benchmarks & Key Results

Rigorous evaluation across real-world drives and 25 synthetic failure test cases demonstrates state-of-the-art dead-reckoning performance on low-cost consumer hardware:

| Benchmark Dimension | Target Specification | Achieved Metric | Status |
| :--- | :--- | :--- | :--- |
| **Inference Latency** | $< 10.0\text{ ms}$ (Real-time limit) | **$0.511\text{ ms}$** per frame (ONNX Runtime) | 🟢 Exceeded (20x faster) |
| **Model Storage Size** | $< 25\text{ MB}$ (Mobile bundle limit) | **$< 2.0\text{ MB}$** (`deep_idr.onnx`) | 🟢 Exceeded |
| **Positional Drift Rate** | $< 3.0\%$ of total distance traveled | **$1.71\%$** average drift across test runs | 🟢 State-of-the-art |
| **Orientation Invariance** | Unaffected by phone tilt/inversion | Full rotational invariance via Gravity Dot Product | 🟢 Verified |
| **Stress Test Pass Rate** | $> 95\%$ | **$100\%$** (25/25 scenarios in `validate_model.py`) | 🟢 Perfect |
| **Zero-Shot Generalization**| Stable on unseen car and driver | Tested on dataset `Y1` without retraining | 🟢 Verified |

---

## 🏁 Summary: How Each Folder Fits the Big Picture

- **`ml/`** is the **brain**: It ingests raw physics data, invents rotation-invariant mathematical features, trains the 1D-CNN, and compiles the lightweight edge ONNX model.
- **`backend/`** is the **control tower**: It manages user authentication, device fleets, model lifecycles, map metadata, remote configs, and API endpoints for analytics and simulations.
- **`simulation/`** is the **virtual proving ground**: It recreates reality in code, simulating road routes, sensor degradation, and massive satellite blackouts to benchmark navigation accuracy before hitting physical roads.
- **`contracts/`** is the **law**: It defines the interfaces, ensuring that the ML model, the backend API, and the mobile edge app speak the exact same data dialect without runtime crashes.
- **`infrastructure/`** is the **launchpad**: It packages the entire backend stack into reproducible Docker containers for one-command deployment anywhere.
- **`docs/`** is the **evidence base**: It catalogs the architecture, empirical benchmarks, and visual trajectory comparisons proving the platform's reliability.
