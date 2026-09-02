# Simulation API Endpoints & Response Schemas Guide

This document defines all REST API endpoints for the **IDR Simulation Engine** (`apps.simulations`), including HTTP methods, URL patterns, query parameters, request bodies, and exact JSON response formats.

---

## 📌 Endpoint Overview Table

| Endpoint Pattern | Method | Description |
| :--- | :--- | :--- |
| [`/api/v1/simulations/presets/`](#1-get-apiv1simulationspresets) | `GET` | Retrieve list of all pre-configured simulation scenario presets |
| [`/api/v1/simulations/`](#2-post-apiv1simulations) | `POST` | Create a new simulation run (Preset or Custom Control Plane) |
| [`/api/v1/simulations/`](#3-get-apiv1simulations) | `GET` | List all historical simulation runs with status and metrics |
| [`/api/v1/simulations/<uuid:pk>/`](#4-get-apiv1simulationsuuidpk) | `GET` | Retrieve detailed status, metrics, and artifact URLs for a specific run |
| [`/api/v1/simulations/<uuid:pk>/run/`](#5-post-apiv1simulationsuuidpkrun) | `POST` | Trigger simulation execution (Asynchronous Celery or Synchronous `?sync=true`) |

---

## 📡 Detailed Endpoint Specifications

### 1. `GET /api/v1/simulations/presets/`
Retrieves a list of all 16 standard pre-configured simulation scenario presets.

- **Method**: `GET`
- **Authentication**: Not required (or Bearer JWT)
- **Headers**: `Accept: application/json`

#### Response (`200 OK`)
```json
[
  {
    "preset_id": "flagship_gnss_outage",
    "name": "SIH-2026 Flagship 300s GNSS Outage Benchmark",
    "description": "Flagship 300-second navigation benchmark with 120-second middle GNSS outage (t=120s to t=240s) for testing dead reckoning position drift and recovery.",
    "duration_seconds": 300.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 42
  },
  {
    "preset_id": "urban_tunnel_outage",
    "name": "Urban Tunnel GNSS Outage",
    "description": "City center route entering a 120s subterranean tunnel with total GNSS signal loss",
    "duration_seconds": 250.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 101
  },
  {
    "preset_id": "highway_corridor",
    "name": "High-Speed Highway Corridor",
    "description": "Suburban expressway navigation at 25 m/s (~90 km/h) testing long-range IMU velocity integration",
    "duration_seconds": 300.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 202
  },
  {
    "preset_id": "urban_canyon_degraded",
    "name": "Urban Canyon Multipath Degradation",
    "description": "High-rise building district creating severe satellite multipath reflection and 15m position jitter",
    "duration_seconds": 200.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 303
  },
  {
    "preset_id": "subway_transfer",
    "name": "Subway & Underground Transit Transfer",
    "description": "Pedestrian descending into metro station concourse with 90s complete blackout",
    "duration_seconds": 180.0,
    "movement_mode": "STOP_AND_GO",
    "seed": 404
  },
  {
    "preset_id": "mountain_winding_road",
    "name": "Mountain Winding Road & Pass",
    "description": "Serpentine mountain highway with continuous sharp turns and periodic hill shading",
    "duration_seconds": 240.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 505
  }
]
```

---

### 2. `POST /api/v1/simulations/`
Creates a new simulation run instance. Supports either a preset scenario reference or a custom frontend Control Plane payload.

- **Method**: `POST`
- **Headers**: `Content-Type: application/json`

#### Request JSON (Preset Mode)
```json
{
  "preset_id": "urban_tunnel_outage",
  "seed": 42,
  "duration_seconds": 250.0
}
```

#### Request JSON (Custom Frontend Control Plane Mode)
```json
{
  "custom_scenario": {
    "scenario_id": "custom_route_001",
    "name": "New Delhi Central Ridge Route",
    "duration_seconds": 180.0,
    "timestep_seconds": 0.01,
    "seed": 42,
    "initial_state": {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "altitude": 216.0,
      "velocity_mps": 10.0,
      "heading_deg": 45.0
    },
    "waypoints": [
      [0.0, 0.0],
      [200.0, 200.0],
      [500.0, 200.0]
    ],
    "imu": {
      "accelerometer_hz": 100.0,
      "gyroscope_hz": 100.0,
      "accel_noise_std": 0.05,
      "gyro_noise_std": 0.005
    },
    "gnss": {
      "frequency_hz": 1.0,
      "position_noise_meters": 3.0,
      "outages": [
        {
          "start_seconds": 40.0,
          "end_seconds": 120.0
        }
      ]
    }
  }
}
```

#### Response (`201 Created`)
```json
{
  "id": "e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "seed": 42,
  "duration_seconds": 250.0,
  "status": "CREATED",
  "scenario_config": {
    "scenario_id": "urban_tunnel_outage",
    "name": "Urban Tunnel GNSS Outage",
    "duration_seconds": 250.0,
    "timestep_seconds": 0.01,
    "seed": 42,
    "initial_state": {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "altitude": 400.0,
      "velocity_mps": 11.1,
      "heading_deg": 45.0
    },
    "waypoints": [[0, 0], [250, 250], [600, 250], [900, 500]],
    "gnss": {
      "frequency_hz": 1.0,
      "position_noise_meters": 2.5,
      "outages": [{"start_seconds": 50.0, "end_seconds": 170.0}]
    }
  },
  "metrics": {},
  "gnss_outage_evaluations": [],
  "artifact_paths": {},
  "error_message": "",
  "created_at": "2026-09-02T16:00:00.000Z",
  "started_at": null,
  "completed_at": null
}
```

---

### 3. `GET /api/v1/simulations/`
Lists all simulation runs stored in PostgreSQL, ordered by creation date descending.

- **Method**: `GET`
- **Headers**: `Accept: application/json`

#### Response (`200 OK`)
```json
[
  {
    "id": "e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b",
    "scenario_id": "urban_tunnel_outage",
    "scenario_name": "Urban Tunnel GNSS Outage",
    "seed": 42,
    "duration_seconds": 250.0,
    "status": "COMPLETED",
    "scenario_config": { ... },
    "metrics": {
      "travelled_distance_m": 1250.45,
      "rmse_position_m": 412.35,
      "mean_position_error_m": 350.12,
      "final_position_error_m": 650.80,
      "max_position_error_m": 658.20,
      "drift_percentage": 52.05
    },
    "gnss_outage_evaluations": [
      {
        "start_seconds": 50.0,
        "end_seconds": 170.0,
        "duration_seconds": 120.0,
        "initial_error_m": 12.4,
        "final_error_m": 620.5,
        "max_error_m": 658.2,
        "drift_rate_m_per_s": 5.06
      }
    ],
    "artifact_paths": {
      "ground_truth_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/ground_truth.csv",
      "sensor_stream_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/sensor_stream.csv",
      "evaluation_report_json": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/evaluation_report.json"
    },
    "error_message": "",
    "created_at": "2026-09-02T16:00:00.000Z",
    "started_at": "2026-09-02T16:00:01.000Z",
    "completed_at": "2026-09-02T16:00:03.000Z"
  }
]
```

---

### 4. `GET /api/v1/simulations/<uuid:pk>/`
Retrieves detailed status, execution timestamps, metrics summary, and download URLs for a specific simulation run.

- **Method**: `GET`
- **Path Parameters**: `pk` (UUID)

#### Response (`200 OK`)
```json
{
  "id": "e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "seed": 42,
  "duration_seconds": 250.0,
  "status": "COMPLETED",
  "scenario_config": { ... },
  "metrics": {
    "travelled_distance_m": 1250.45,
    "rmse_position_m": 412.35,
    "mean_position_error_m": 350.12,
    "final_position_error_m": 650.80,
    "max_position_error_m": 658.20,
    "drift_percentage": 52.05
  },
  "gnss_outage_evaluations": [
    {
      "start_seconds": 50.0,
      "end_seconds": 170.0,
      "duration_seconds": 120.0,
      "initial_error_m": 12.4,
      "final_error_m": 620.5,
      "max_error_m": 658.2,
      "drift_rate_m_per_s": 5.06
    }
  ],
  "artifact_paths": {
    "ground_truth_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/ground_truth.csv",
    "sensor_stream_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/sensor_stream.csv",
    "evaluation_report_json": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/evaluation_report.json"
  },
  "error_message": "",
  "created_at": "2026-09-02T16:00:00.000Z",
  "started_at": "2026-09-02T16:00:01.000Z",
  "completed_at": "2026-09-02T16:00:03.000Z"
}
```

#### Error Response (`404 Not Found`)
```json
{
  "error": {
    "code": "SIMULATION_NOT_FOUND",
    "message": "Simulation run not found."
  }
}
```

---

### 5. `POST /api/v1/simulations/<uuid:pk>/run/`
Triggers execution of the simulation job.

- **Method**: `POST`
- **Query Parameters**:
  - `sync=true`: Runs synchronously in the HTTP thread (returns when completed).
  - `sync=false` (default): Queues job asynchronously via Celery worker.

#### Response (`200 OK`)
```json
{
  "id": "e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "seed": 42,
  "duration_seconds": 250.0,
  "status": "COMPLETED",
  "metrics": {
    "travelled_distance_m": 1250.45,
    "rmse_position_m": 412.35,
    "mean_position_error_m": 350.12,
    "final_position_error_m": 650.80,
    "max_position_error_m": 658.20,
    "drift_percentage": 52.05
  },
  "gnss_outage_evaluations": [
    {
      "start_seconds": 50.0,
      "end_seconds": 170.0,
      "duration_seconds": 120.0,
      "initial_error_m": 12.4,
      "final_error_m": 620.5,
      "max_error_m": 658.2,
      "drift_rate_m_per_s": 5.06
    }
  ],
  "artifact_paths": {
    "ground_truth_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/ground_truth.csv",
    "sensor_stream_csv": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/sensor_stream.csv",
    "evaluation_report_json": "http://127.0.0.1:8000/media/simulations/e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b/evaluation_report.json"
  },
  "error_message": "",
  "created_at": "2026-09-02T16:00:00.000Z",
  "started_at": "2026-09-02T16:00:01.000Z",
  "completed_at": "2026-09-02T16:00:03.000Z"
}
```
