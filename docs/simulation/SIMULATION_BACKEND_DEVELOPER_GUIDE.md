# IDR Simulation Backend Integration Guide (Developer-to-Developer Handover)

**Target Audience:** Simulation Backend Engineer / Control Plane Developer  
**System:** Intelligent Dead Reckoning (IDR) Mobile Core Engine  
**Host Port:** `http://localhost:8088` (Default Unified Backend Port)  
**Date:** September 2, 2026  

---

## 📌 Executive Summary & Architecture Role

Welcome to the IDR Simulation Engine Integration! As the **Simulation Backend Engineer**, your component generates synthetic vehicle motion dynamics, sensor streams (100 Hz IMU accel/gyro/mag), and controlled GNSS outage scenarios (e.g. subterranean tunnels, urban canyons).

The Mobile Backend engine processes your synthetic streams using the **exact same C++ physics and 13-state EKF fusion pipeline** as real smartphone hardware.

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                      SIMULATION BACKEND DATA LIFECYCLE                      │
 └─────────────────────────────────────────────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │ 1. FETCH PRESETS & CONFIGURATIONS                                           │
 │ • GET /api/v1/simulations/presets/                                          │
 │ • Retrieve the 6 standard benchmark scenarios (Flagship, Tunnel, Highway).  │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │ 2. TIME-SERIES PREVIEW & STREAM GENERATION                                  │
 │ • GET /api/v1/simulations/preview?preset_id=urban_tunnel_outage             │
 │ • Inspect 100 Hz sensor frames & ground-truth reference trajectory.        │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │ 3. STREAM SENSOR DATA TO UNIFIED INGESTION GATEWAY                          │
 │ • POST /api/v1/get_imu                                                      │
 │ • Stream single frames or batch time-series arrays to C++ engine.          │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │ 4. TRIGGER BENCHMARK EXECUTION & READ EVALUATION METRICS                    │
 │ • POST /api/v1/simulations/<id>/run/                                        │
 │ • Read RMSE position error, max drift (m), and drift rate (m/s).            │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Integration Workflow

---

### STEP 1: Fetch Scenario Presets (`GET /api/v1/simulations/presets/`)

Call this endpoint to list all pre-configured benchmark scenarios:

- **HTTP Method:** `GET`
- **URL:** `http://localhost:8088/api/v1/simulations/presets/`

#### Expected Response (`200 OK`):
```json
[
  {
    "preset_id": "flagship_gnss_outage",
    "name": "SIH-2026 Flagship 300s GNSS Outage Benchmark",
    "description": "Flagship 300-second navigation benchmark with 120-second middle GNSS outage (t=120s to t=240s) for testing dead reckoning position drift and recovery.",
    "duration_seconds": 300.0,
    "outage_start_s": 120.0,
    "outage_end_s": 240.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 42
  },
  {
    "preset_id": "urban_tunnel_outage",
    "name": "Urban Tunnel GNSS Outage",
    "description": "City center route entering a 120s subterranean tunnel with total GNSS signal loss (t=50s to t=170s).",
    "duration_seconds": 250.0,
    "outage_start_s": 50.0,
    "outage_end_s": 170.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 101
  }
]
```

---

### STEP 2: Request Time-Series Preview (`GET /api/v1/simulations/preview`)

Before launching a full run, fetch time-series preview frames to inspect ground truth, synthetic IMU samples, and outage boundaries:

- **HTTP Method:** `GET`
- **URL Pattern:** `http://localhost:8088/api/v1/simulations/preview?preset_id=<preset_id>&samples=<N>&step_interval_s=1.0`

#### Example Call:
`GET http://localhost:8088/api/v1/simulations/preview?preset_id=urban_tunnel_outage&samples=3`

#### Expected Response (`200 OK`):
```json
{
  "status": "SUCCESS",
  "preset_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "duration_seconds": 250.0,
  "outage_start_s": 50.0,
  "outage_end_s": 170.0,
  "sampling_frequency_hz": 1.0,
  "total_frames_returned": 3,
  "time_series": [
    {
      "sequence_index": 0,
      "t_offset_s": 0.0,
      "timestamp_ms": 1746000000000,
      "ground_truth": {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "speed_mps": 12.5,
        "heading_deg": 45.0
      },
      "gnss": {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.5, 0.0, 9.807],
        "gyro_rad_s": [0.0, 0.0, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": { "pitch": 5.0, "roll": 0.0, "yaw": 45.0 }
      },
      "calculated_navigation_state": {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    }
  ]
}
```

---

### STEP 3: Stream Sensor Data to Unified Endpoint (`POST /api/v1/get_imu`)

This is the **single common endpoint** for sending IMU + GNSS frame data to the engine. You can send **Single Frame** objects OR **Time-Series Batch Arrays**.

- **HTTP Method:** `POST`
- **URL:** `http://localhost:8088/api/v1/get_imu`
- **Header:** `Content-Type: application/json`

#### A. Single Frame Payload Schema:
```json
{
  "source_mode": "SIMULATION",
  "timestamp_ms": 1746000000000,
  "gnss": {
    "latitude": 13.0827,
    "longitude": 80.2707,
    "altitude": 920.4,
    "speed_mps": 10.014,
    "heading_deg": 0.0488,
    "accuracy_m": 1.2,
    "satellites": 14,
    "status": "LOCKED",
    "valid": true
  },
  "imu": {
    "accel_m_s2": [0.500, 0.000, 10.661],
    "gyro_rad_s": [0.000, 0.000, 0.087],
    "mag_uT": [22.40, -14.20, 41.80],
    "orientation_deg": {
      "pitch": 5.0,
      "roll": 0.0,
      "yaw": 0.0
    }
  }
}
```

#### B. Time-Series Batch Array Payload Schema:
```json
{
  "source_mode": "SIMULATION",
  "time_series": [
    {
      "t_offset_s": 0.0,
      "timestamp_ms": 1746000000000,
      "gnss": { "latitude": 13.0827, "longitude": 80.2707, "speed_mps": 10.014, "heading_deg": 0.05, "valid": true },
      "imu": { "accel_m_s2": [0.50, 0.00, 10.66], "gyro_rad_s": [0.00, 0.00, 0.087], "mag_uT": [22.4, -14.2, 41.8] }
    },
    {
      "t_offset_s": 1.0,
      "timestamp_ms": 1746000001000,
      "gnss": { "latitude": 13.0828, "longitude": 80.2708, "speed_mps": 10.20, "heading_deg": 0.05, "valid": true },
      "imu": { "accel_m_s2": [0.52, 0.01, 10.55], "gyro_rad_s": [0.00, 0.00, 0.085], "mag_uT": [22.4, -14.2, 41.8] }
    }
  ]
}
```

---

### STEP 4: Trigger Execution & Read Metrics (`POST /api/v1/simulations/<uuid:id>/run/`)

After creating a run, trigger benchmark execution to evaluate Dead Reckoning drift rates during GNSS outages:

- **HTTP Method:** `POST`
- **URL:** `http://localhost:8088/api/v1/simulations/<run_id>/run/`

#### Expected Response (`200 OK`):
```json
{
  "id": "e4f8b91a-2c3d-4e5f-9a0b-1c2d3e4f5a6b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "status": "COMPLETED",
  "metrics": {
    "travelled_distance_m": 1250.45,
    "rmse_position_m": 14.85,
    "mean_position_error_m": 12.40,
    "final_position_error_m": 13.85,
    "max_position_error_m": 24.50,
    "drift_percentage": 2.31
  },
  "gnss_outage_evaluations": [
    {
      "start_seconds": 50.0,
      "end_seconds": 170.0,
      "duration_seconds": 120.0,
      "initial_error_m": 1.2,
      "final_error_m": 13.85,
      "max_error_m": 24.5,
      "drift_rate_m_per_s": 0.115
    }
  ],
  "started_at": "2026-09-02T16:30:00Z",
  "completed_at": "2026-09-02T16:30:02Z"
}
```

---

## 💻 Code Integration Examples for Co-Developer

### Python Example (`requests`):
```python
import requests
import time

BASE_URL = "http://localhost:8088"

# 1. Fetch available presets
presets = requests.get(f"{BASE_URL}/api/v1/simulations/presets/").json()
print("Available Presets:", [p['preset_id'] for p in presets])

# 2. Get 5-frame preview for urban_tunnel_outage
preview = requests.get(f"{BASE_URL}/api/v1/simulations/preview?preset_id=urban_tunnel_outage&samples=5").json()
print(f"Retrieved {preview['total_frames_returned']} preview frames")

# 3. Stream a simulated sensor frame to unified endpoint
payload = {
    "source_mode": "SIMULATION",
    "timestamp_ms": int(time.time() * 1000),
    "gnss": {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "valid": True
    },
    "imu": {
        "accel_m_s2": [0.50, 0.00, 9.807],
        "gyro_rad_s": [0.00, 0.00, 0.00],
        "mag_uT": [22.4, -14.2, 41.8]
    }
}
res = requests.post(f"{BASE_URL}/api/v1/get_imu", json=payload).json()
print("Engine Output Navigation State:", res["calculated_navigation_state"])
```

### TypeScript / JavaScript Example (`axios` / `fetch`):
```typescript
import axios from 'axios';

const BASE_URL = 'http://localhost:8088';

async function runSimulationFlow() {
  // 1. Fetch scenario presets
  const presetsRes = await axios.get(`${BASE_URL}/api/v1/simulations/presets/`);
  console.log('Presets:', presetsRes.data);

  // 2. Stream IMU batch to unified endpoint
  const batchPayload = {
    source_mode: 'SIMULATION',
    time_series: [
      {
        t_offset_s: 0.0,
        timestamp_ms: Date.now(),
        gnss: { latitude: 13.0827, longitude: 80.2707, speed_mps: 10.0, heading_deg: 45.0, valid: true },
        imu: { accel_m_s2: [0.5, 0.0, 9.81], gyro_rad_s: [0.0, 0.0, 0.0], mag_uT: [22.4, -14.2, 41.8] }
      }
    ]
  };

  const response = await axios.post(`${BASE_URL}/api/v1/get_imu`, batchPayload);
  console.log('Processed Navigation Output:', response.data);
}

runSimulationFlow();
```
