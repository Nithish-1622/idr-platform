# Running Simulations & API Guide

## 1. Running Simulations via Python API

```python
from simulation.scenario.presets import get_preset_scenarios
from simulation.runner.engine import SimulationEngine

presets = get_preset_scenarios()
scenario = presets["flagship_gnss_outage"]

engine = SimulationEngine(scenario)
results = engine.run(output_dir="media/simulations/my_run")

print("RMSE Position:", results["result"]["metrics"]["rmse_position_m"])
print("Drift %:", results["result"]["metrics"]["drift_percentage"])
```

---

## 2. Running Simulations via Django REST API

### Create Simulation Job
```http
POST /api/v1/simulations/
Content-Type: application/json

{
  "preset_id": "flagship_gnss_outage",
  "seed": 42,
  "duration_seconds": 300.0
}
```

### Trigger Simulation Execution (Asynchronous via Celery)
```http
POST /api/v1/simulations/<id>/run/
```

### Retrieve Simulation Status & Evaluation Results
```http
GET /api/v1/simulations/<id>/
```

---

## 3. Flagship SIH Benchmark Scenario

- **Scenario ID**: `flagship_gnss_outage`
- **Duration**: 300.0 seconds (5 minutes)
- **Timestep**: 0.01 seconds (100Hz IMU, 1Hz GNSS)
- **Outage Window**: $t=120\text{s}$ to $t=240\text{s}$ (2-minute complete GNSS loss)
- **Primary Goal**: Evaluates IDR dead-reckoning drift growth during GNSS outage and recovery behavior after signal restoration.
