# Simulation Engine Architecture

The **IDR Simulation Engine** is a scientifically defensible, deterministic simulation and evaluation system designed to test smartphone-based Intelligent Dead Reckoning (IDR) navigation algorithms.

---

## 🏛️ Architectural Principles

1. **Decoupled Execution**: The Simulation Engine operates completely outside the HTTP request loop and mobile navigation runtime.
2. **Immutability of Ground Truth**: Ground Truth physical state is pristine. Disturbances (noise, bias, drift, outages) are applied only to generated sensor observations.
3. **Local Cartesian Coordinates (ENU)**: Physics and kinematics are computed in local East-North-Up (ENU) meters $(x, y, z)$. Geographic WGS-84 coordinates are derived at boundaries.
4. **Deterministic Reproducibility**: Using explicit random seeds (`seed=42`), any scenario execution produces bit-identical sensor streams across runs.
5. **Contract Enforcement**: Output sensor streams conform to `contracts/sensor/schema.json` and estimated navigation state streams conform to `contracts/navigation-state/schema.json`.

---

## 🔄 Simulation Pipeline Flow

```text
Scenario Definition
        ↓
Scenario Validation
        ↓
Trajectory Generator (ENU Physics)
        ↓
Ground Truth Time-Series
        ↓
Sensor Models (IMU, GNSS, Magnetometer)
        ↓
Disturbance Engine (Noise, Bias, Drift, Dropouts)
        ↓
Simulated Sensor Stream
        ↓
IDR Pipeline Adapter (ReferenceONNXIDRAdapter using deep_idr.onnx)
        ↓
Estimated Navigation State
        ↓
Evaluation Engine (RMSE, FPE, Drift %, Outage Metrics)
        ↓
Artifact Storage & PostgreSQL Job Status
```
