# IDR Master API Specification, Scenario Data Flow & Complete JSON Schemas

**SIH-2026 Intelligent Dead Reckoning (IDR) Navigation System**  
*Exhaustive Developer Implementation Manual & Endpoint Contract Guide*

---

## 1. Network Architecture & Endpoint Directory

| # | Endpoint Path | HTTP Method | Target Server URL Variable | Description |
| :- | :--- | :- | :--- | :--- |
| **1** | `/health` | `GET` | `{{IDR_BACKEND_BASE_URL}}` | System health checkup & module statuses |
| **2** | `/api/v1/simulations/presets/` | `GET` | `{{SIMULATION_BACKEND_URL}}` | List all 6 pre-configured scenario presets |
| **3** | `/api/v1/simulations/preview` | `GET` | `{{SIMULATION_BACKEND_URL}}` | Fetch time-series synthetic sensor preview stream |
| **4** | `/api/v1/simulations/preview` | `POST` | `{{SIMULATION_BACKEND_URL}}` | Generate custom time-series preview stream |
| **5** | `/api/v1/simulations/` | `POST` | `{{SIMULATION_BACKEND_URL}}` | Create simulation benchmark run instance |
| **6** | `/api/v1/simulations/` | `GET` | `{{SIMULATION_BACKEND_URL}}` | List all created simulation runs |
| **7** | `/api/v1/simulations/<id>/run/` | `POST` | `{{SIMULATION_BACKEND_URL}}` | Execute simulation run & calculate RMSE metrics |
| **8** | `/api/v1/models/latest/contract/` | `GET` | `{{SIMULATION_BACKEND_URL}}` | ONNX model version contract & metadata JSON |
| **9** | `/api/v1/models/latest/download/` | `GET` | `{{SIMULATION_BACKEND_URL}}` | Stream raw binary `.onnx` model file |
| **10** | `/api/v1/get_imu` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Unified gateway (INS physics + ONNX + EKF fusion) |
| **11** | `/onnx/inference` | `POST` | `{{SIMULATION_BACKEND_URL}}` | ONNX model inference runner (19-in / 7-out) |
| **12** | `/fusion/update` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | 13-state Extended Kalman Filter update step |
| **13** | `/events/vibration` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Report road pothole / shock vibration event |
| **14** | `/events/turn` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Report vehicle turning maneuver event |
| **15** | `/events/road-disturbance` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Report speed bump disturbance event |
| **16** | `/trajectory/observation` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Upload raw trajectory observation samples |
| **17** | `/dr/error` | `POST` | `{{IDR_BACKEND_BASE_URL}}` | Report Shadow DR drift error statistics |
| **18** | `/road/context` | `GET` | `{{IDR_BACKEND_BASE_URL}}` | Fetch contextual road map-matching intelligence |

---

## 2. Scenario Identification (`preset_id`)

When a user selects any card on the Mobile App Dashboard, the system identifies the target scenario using its unique `preset_id`:

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
  },
  {
    "preset_id": "highway_corridor",
    "name": "High-Speed Highway Corridor",
    "description": "Suburban expressway navigation at 25 m/s (~90 km/h) testing long-range IMU velocity integration.",
    "duration_seconds": 300.0,
    "outage_start_s": 100.0,
    "outage_end_s": 200.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 202
  },
  {
    "preset_id": "urban_canyon_degraded",
    "name": "Urban Canyon Multipath Degradation",
    "description": "High-rise building district creating severe satellite multipath reflection and 15m position jitter.",
    "duration_seconds": 200.0,
    "outage_start_s": 60.0,
    "outage_end_s": 140.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 303
  },
  {
    "preset_id": "subway_transfer",
    "name": "Subway & Underground Transit Transfer",
    "description": "Pedestrian descending into metro station concourse with 90s complete blackout.",
    "duration_seconds": 180.0,
    "outage_start_s": 45.0,
    "outage_end_s": 135.0,
    "movement_mode": "STOP_AND_GO",
    "seed": 404
  },
  {
    "preset_id": "mountain_winding_road",
    "name": "Mountain Winding Road & Pass",
    "description": "Serpentine mountain highway with continuous sharp turns and periodic hill shading.",
    "duration_seconds": 240.0,
    "outage_start_s": 80.0,
    "outage_end_s": 160.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 505
  }
]
```

---

## 3. Exhaustive Endpoint Contracts & Complete JSON Schemas

### Endpoint 1: System Health Checkup
- **HTTP Method**: `GET`
- **Path**: `/health` or `/api/v1/health`
- **Target URL**: `{{IDR_BACKEND_BASE_URL}}/health`
- **Request Headers**: None required
- **Response Headers**: `Content-Type: application/json`, `Access-Control-Allow-Origin: *`

#### Complete JSON Response (`200 OK`):
```json
{
  "status": "HEALTHY",
  "engine": "IDR C++ Core Backend Engine (mobile-backend v1.0.0)",
  "common_endpoint": "POST /api/v1/get_imu",
  "friend_simulation_url": "http://10.57.1.175:8000",
  "local_engine_port": 8088,
  "modules": {
    "ins_mechanization": "ACTIVE (100Hz Physics Double Integration)",
    "onnx_model_manager": "ACTIVE (19-in / 7-out ONNX Model)",
    "error_state_ekf": "ACTIVE (13-State ESKF Fusion)",
    "rolling_window": "ACTIVE (20-min History Window)",
    "gnss_monitor": "ACTIVE (4-State Monitor)"
  },
  "timestamp_ms": 1746000000000
}
```

---

### Endpoint 2: GET Simulation Scenario Presets
- **HTTP Method**: `GET`
- **Path**: `/api/v1/simulations/presets` or `/api/v1/simulations/presets/`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/simulations/presets/`
- **Request Headers**: `Content-Type: application/json`

#### Complete JSON Response (`200 OK`):
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
  },
  {
    "preset_id": "highway_corridor",
    "name": "High-Speed Highway Corridor",
    "description": "Suburban expressway navigation at 25 m/s (~90 km/h) testing long-range IMU velocity integration.",
    "duration_seconds": 300.0,
    "outage_start_s": 100.0,
    "outage_end_s": 200.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 202
  },
  {
    "preset_id": "urban_canyon_degraded",
    "name": "Urban Canyon Multipath Degradation",
    "description": "High-rise building district creating severe satellite multipath reflection and 15m position jitter.",
    "duration_seconds": 200.0,
    "outage_start_s": 60.0,
    "outage_end_s": 140.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 303
  },
  {
    "preset_id": "subway_transfer",
    "name": "Subway & Underground Transit Transfer",
    "description": "Pedestrian descending into metro station concourse with 90s complete blackout.",
    "duration_seconds": 180.0,
    "outage_start_s": 45.0,
    "outage_end_s": 135.0,
    "movement_mode": "STOP_AND_GO",
    "seed": 404
  },
  {
    "preset_id": "mountain_winding_road",
    "name": "Mountain Winding Road & Pass",
    "description": "Serpentine mountain highway with continuous sharp turns and periodic hill shading.",
    "duration_seconds": 240.0,
    "outage_start_s": 80.0,
    "outage_end_s": 160.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 505
  }
]
```

---

### Endpoint 3: GET Time-Series Trajectory Stream Preview
- **HTTP Method**: `GET`
- **Path**: `/api/v1/simulations/preview`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/simulations/preview?preset_id=urban_tunnel_outage&samples=5&step_interval_s=1.0`
- **Query Parameters**:
  - `preset_id`: ID of the scenario (`urban_tunnel_outage`)
  - `samples`: Number of sequential frame samples (e.g. `5` or `40`)
  - `step_interval_s`: Time step interval in seconds (e.g. `1.0`)

#### Complete JSON Response (`200 OK`):
```json
{
  "status": "SUCCESS",
  "preset_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "duration_seconds": 250.0,
  "outage_start_s": 50.0,
  "outage_end_s": 170.0,
  "sampling_frequency_hz": 1.0,
  "total_frames_returned": 5,
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
        "accel_m_s2": [0.5, 0.0, 9.80665],
        "gyro_rad_s": [0.0, 0.0, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      },
      "calculated_navigation_state": {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "ekf_position_sigma_m": 2.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    },
    {
      "sequence_index": 1,
      "t_offset_s": 1.0,
      "timestamp_ms": 1746000001000,
      "ground_truth": {
        "latitude": 13.08277947,
        "longitude": 80.27077947,
        "speed_mps": 12.5,
        "heading_deg": 45.0
      },
      "gnss": {
        "latitude": 13.08277947,
        "longitude": 80.27077947,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.538, 0.022, 9.878],
        "gyro_rad_s": [0.0005, 0.0011, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      },
      "calculated_navigation_state": {
        "latitude": 13.08277947,
        "longitude": 80.27077947,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "ekf_position_sigma_m": 2.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    },
    {
      "sequence_index": 2,
      "t_offset_s": 2.0,
      "timestamp_ms": 1746000002000,
      "ground_truth": {
        "latitude": 13.08285894,
        "longitude": 80.27085894,
        "speed_mps": 12.5,
        "heading_deg": 45.0
      },
      "gnss": {
        "latitude": 13.08285894,
        "longitude": 80.27085894,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.567, 0.017, 9.933],
        "gyro_rad_s": [0.0008, -0.0008, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      },
      "calculated_navigation_state": {
        "latitude": 13.08285894,
        "longitude": 80.27085894,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "ekf_position_sigma_m": 2.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    },
    {
      "sequence_index": 3,
      "t_offset_s": 3.0,
      "timestamp_ms": 1746000003000,
      "ground_truth": {
        "latitude": 13.08293841,
        "longitude": 80.27093841,
        "speed_mps": 12.5,
        "heading_deg": 45.0
      },
      "gnss": {
        "latitude": 13.08293841,
        "longitude": 80.27093841,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.579, -0.039, 9.956],
        "gyro_rad_s": [0.001, -0.0019, 0.087266],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      },
      "calculated_navigation_state": {
        "latitude": 13.08293841,
        "longitude": 80.27093841,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "ekf_position_sigma_m": 2.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    },
    {
      "sequence_index": 4,
      "t_offset_s": 4.0,
      "timestamp_ms": 1746000004000,
      "ground_truth": {
        "latitude": 13.08301788,
        "longitude": 80.27101788,
        "speed_mps": 12.5,
        "heading_deg": 45.0
      },
      "gnss": {
        "latitude": 13.08301788,
        "longitude": 80.27101788,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.573, -0.026, 9.943],
        "gyro_rad_s": [0.0009, -0.0013, 0.087266],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      },
      "calculated_navigation_state": {
        "latitude": 13.08301788,
        "longitude": 80.27101788,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.98,
        "drift_estimate_m": 0.0,
        "ekf_position_sigma_m": 2.0,
        "navigation_mode": "GNSS_INS",
        "is_dr_mode": false
      }
    }
  ]
}
```

---

### Endpoint 4: POST Create Simulation Benchmark Run Instance
- **HTTP Method**: `POST`
- **Path**: `/api/v1/simulations/` or `/api/v1/simulations`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/simulations/`

#### Complete JSON Request Body:
```json
{
  "preset_id": "urban_tunnel_outage",
  "seed": 42,
  "duration_seconds": 250.0
}
```

#### Complete JSON Response Body (`201 Created`):
```json
{
  "id": "e4f812a0-81b3-4c90-bdf1-99511a2f601b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "seed": 42,
  "duration_seconds": 250.0,
  "status": "CREATED",
  "scenario_config": {
    "preset_id": "urban_tunnel_outage",
    "name": "Urban Tunnel GNSS Outage",
    "description": "City center route entering a 120s subterranean tunnel with total GNSS signal loss (t=50s to t=170s).",
    "duration_seconds": 250.0,
    "outage_start_s": 50.0,
    "outage_end_s": 170.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 101
  },
  "metrics": {},
  "gnss_outage_evaluations": [],
  "created_at": "2026-09-02T19:46:00Z"
}
```

---

### Endpoint 5: POST Execute Simulation Run & Compute RMSE Metrics
- **HTTP Method**: `POST`
- **Path**: `/api/v1/simulations/<run_id>/run/`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/simulations/e4f812a0-81b3-4c90-bdf1-99511a2f601b/run/`

#### Complete JSON Response Body (`200 OK`):
```json
{
  "id": "e4f812a0-81b3-4c90-bdf1-99511a2f601b",
  "scenario_id": "urban_tunnel_outage",
  "scenario_name": "Urban Tunnel GNSS Outage",
  "seed": 42,
  "duration_seconds": 250.0,
  "status": "COMPLETED",
  "scenario_config": {
    "preset_id": "urban_tunnel_outage",
    "name": "Urban Tunnel GNSS Outage",
    "description": "City center route entering a 120s subterranean tunnel with total GNSS signal loss (t=50s to t=170s).",
    "duration_seconds": 250.0,
    "outage_start_s": 50.0,
    "outage_end_s": 170.0,
    "movement_mode": "WAYPOINT_ROUTE",
    "seed": 101
  },
  "metrics": {
    "travelled_distance_m": 1250.45,
    "rmse_position_m": 14.85,
    "mean_position_error_m": 12.4,
    "final_position_error_m": 13.85,
    "max_position_error_m": 24.5,
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
  "created_at": "2026-09-02T19:46:00Z",
  "started_at": "2026-09-02T19:46:01Z",
  "completed_at": "2026-09-02T19:46:01Z"
}
```

---

### Endpoint 6: GET ONNX Model Contract & Metadata Protocol
- **HTTP Method**: `GET`
- **Path**: `/api/v1/models/latest/contract/`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/models/latest/contract/`

#### Complete JSON Response Body (`200 OK`):
```json
{
  "model": {
    "name": "deep_idr_model",
    "version": "1.0.0",
    "format": "ONNX",
    "opset": 14,
    "artifact_url": "http://localhost:8088/api/v1/models/latest/download/",
    "download_url": "http://localhost:8088/api/v1/models/latest/download/",
    "checksum_sha256": "d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980",
    "file_size_bytes": 3072
  },
  "input": {
    "tensor_name": "imu_window",
    "shape": [1, 100, 6],
    "dtype": "float32",
    "channels": [
      "ax",
      "ay",
      "az",
      "gx",
      "gy",
      "gz"
    ],
    "sampling_frequency_hz": 100
  },
  "output": {
    "tensor_name": "delta_pose",
    "shape": [1, 7],
    "dtype": "float32",
    "elements": [
      "v_hat_mps",
      "a_hat_mps2",
      "e_hat_m",
      "p_vibration",
      "p_pothole",
      "p_turn",
      "confidence"
    ]
  },
  "preprocessing": {
    "accel_scale": 1.0,
    "gyro_scale": 1.0,
    "window_size": 100,
    "stride": 10
  }
}
```

---

### Endpoint 7: GET Binary ONNX Stream Download
- **HTTP Method**: `GET`
- **Path**: `/api/v1/models/latest/download/` or `/api/v1/model.onnx`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/api/v1/models/latest/download/`
- **Response Headers**:
  - `Content-Type: application/octet-stream`
  - `Content-Disposition: attachment; filename="deep_idr_model_v1.0.0.onnx"`
  - `Content-Length: 3072`
  - `X-Model-Name: deep_idr_model`
  - `X-Model-Version: 1.0.0`
  - `X-Model-Opset: 14`
  - `X-Model-Checksum-SHA256: d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980`
  - `ETag: "d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980"`

#### Raw Binary Payload (`200 OK`):
```text
ONNX_IDR_MODEL_BINARY_STREAM_V1_0_0\x00\x00... [3072 Bytes]
```

---

### Endpoint 8: Unified Ingestion Gateway (`POST /api/v1/get_imu`)
- **HTTP Method**: `POST`
- **Path**: `/api/v1/get_imu`
- **Target URL**: `{{IDR_BACKEND_BASE_URL}}/api/v1/get_imu`
- **Description**: Receives time-series frames and executes 100 Hz INS physics double integration, ONNX position error drift correction, and 13-state EKF state update.

#### Complete JSON Batch Request Body:
```json
{
  "source_mode": "SIMULATION",
  "time_series": [
    {
      "sequence_index": 0,
      "t_offset_s": 0.0,
      "timestamp_ms": 1746000000000,
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
        "accel_m_s2": [0.5, 0.0, 9.80665],
        "gyro_rad_s": [0.0, 0.0, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      }
    },
    {
      "sequence_index": 1,
      "t_offset_s": 1.0,
      "timestamp_ms": 1746000001000,
      "gnss": {
        "latitude": 13.08277947,
        "longitude": 80.27077947,
        "speed_mps": 12.5,
        "heading_deg": 45.0,
        "hdop": 1.2,
        "satellites": 14,
        "status": "LOCKED",
        "valid": true
      },
      "imu": {
        "accel_m_s2": [0.538, 0.022, 9.878],
        "gyro_rad_s": [0.0005, 0.0011, 0.0],
        "mag_uT": [22.4, -14.2, 41.8],
        "orientation_deg": {
          "pitch": 5.0,
          "roll": 0.0,
          "yaw": 45.0
        }
      }
    }
  ]
}
```

#### Complete JSON Batch Response Body (`200 OK`):
```json
{
  "status": "SUCCESS",
  "common_endpoint": "/api/v1/get_imu",
  "mode": "TIME_SERIES_BATCH",
  "processed_frames_count": 2,
  "frames": [
    {
      "t_offset_s": 0.0,
      "timestamp_ms": 1746000000000,
      "calculated_navigation_state": {
        "latitude": 13.08270157,
        "longitude": 80.27070014,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.6636,
        "drift_estimate_m": 13.85,
        "navigation_mode": "GNSS_INS"
      }
    },
    {
      "t_offset_s": 1.0,
      "timestamp_ms": 1746000001000,
      "calculated_navigation_state": {
        "latitude": 13.08278104,
        "longitude": 80.27077961,
        "speed_kmh": 45.0,
        "heading_deg": 45.0,
        "confidence_score": 0.6636,
        "drift_estimate_m": 13.85,
        "navigation_mode": "GNSS_INS"
      }
    }
  ]
}
```

---

### Endpoint 9: ONNX Model Inference (`POST /onnx/inference`)
- **HTTP Method**: `POST`
- **Path**: `/onnx/inference` or `/onnx/inference-demo`
- **Target URL**: `{{SIMULATION_BACKEND_URL}}/onnx/inference`

#### Complete JSON Request Body:
```json
{
  "feature_tensor": [
    1.407, 0.0, 0.769, 10.576,
    0.0, 0.0, 0.085, 0.085,
    0.15, 0.42, 0.18, 0.00085,
    10.014, 13.85,
    10.2, 0.05, 0.38, 0.008, 12.4
  ],
  "tensor_shape": [1, 19]
}
```

#### Complete JSON Response Body (`200 OK`):
```json
{
  "v_hat_mps": 10.014,
  "a_hat_mps2": 1.407,
  "e_hat_m": 13.85,
  "p_vibration": 0.18,
  "p_pothole": 0.05,
  "p_turn": 0.08,
  "confidence": 0.85,
  "status": "INFERENCE_SUCCESS"
}
```

---

### Endpoint 10: 13-State EKF Fusion Step (`POST /fusion/update`)
- **HTTP Method**: `POST`
- **Path**: `/fusion/update`
- **Target URL**: `{{IDR_BACKEND_BASE_URL}}/fusion/update`

#### Complete JSON Request Body:
```json
{
  "gnss_valid": true,
  "onnx_v_hat": 10.014,
  "onnx_confidence": 0.85,
  "nhc_enabled": true
}
```

#### Complete JSON Response Body (`200 OK`):
```json
{
  "latitude": 13.08279625,
  "longitude": 80.27070004,
  "speed_kmh": 36.05,
  "heading_deg": 0.05,
  "confidence_score": 0.85,
  "drift_estimate_m": 13.85,
  "navigation_mode": "GNSS_INS",
  "is_dr_mode": false,
  "status": "FUSION_SUCCESS"
}
```

---

### Endpoint 11: Report Pothole Vibration Event (`POST /events/vibration`)
- **HTTP Method**: `POST`
- **Path**: `/events/vibration`
- **Target URL**: `{{IDR_BACKEND_BASE_URL}}/events/vibration`

#### Complete JSON Request Body:
```json
{
  "lat": 13.0827,
  "lon": 80.2707,
  "confidence": 0.89,
  "type": "pothole",
  "vibration_rms": 4.25,
  "timestamp": 1746000300000
}
```

#### Complete JSON Response Body (`200 OK`):
```json
{
  "status": "ACKNOWLEDGED",
  "event": "VIBRATION_RECORDED",
  "event_id": "vib_901"
}
```

---

### Endpoint 12: Contextual Road Intelligence (`GET /road/context`)
- **HTTP Method**: `GET`
- **Path**: `/road/context`
- **Target URL**: `{{IDR_BACKEND_BASE_URL}}/road/context?lat=13.0827&lon=80.2707`

#### Complete JSON Response Body (`200 OK`):
```json
{
  "latitude": 13.0827,
  "longitude": 80.2707,
  "road_type": "primary",
  "speed_limit_kph": 60,
  "known_potholes_count": 2,
  "historical_dr_error_mean": 12.4,
  "status": "SUCCESS"
}
```
