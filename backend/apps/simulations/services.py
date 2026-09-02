import uuid
from typing import Any, Dict

from simulation.scenario.presets import get_preset_scenarios
from simulation.scenario.schema import (
    GNSSConfig,
    GNSSOutage,
    IMUConfig,
    InitialState,
    MovementMode,
    SimulationScenario,
)
from .models import SimulationRun
from .tasks import run_simulation_job_task


def create_simulation_run_service(data: Dict[str, Any]) -> SimulationRun:
    custom_config = data.get("custom_scenario") or data.get("scenario_config")

    if custom_config and isinstance(custom_config, dict):
        scenario_id = custom_config.get("scenario_id", f"custom_{uuid.uuid4().hex[:8]}")
        name = custom_config.get("name", "Custom Map Simulation")
        duration = float(custom_config.get("duration_seconds", 300.0))
        seed = int(custom_config.get("seed", data.get("seed", 42)))

        init_st = custom_config.get("initial_state", {})
        initial_state = InitialState(
            latitude=float(init_st.get("latitude", 11.0168)),
            longitude=float(init_st.get("longitude", 76.9558)),
            altitude=float(init_st.get("altitude", 400.0)),
            velocity_mps=float(init_st.get("velocity_mps", 5.0)),
            heading_deg=float(init_st.get("heading_deg", 90.0)),
        )

        waypoints = custom_config.get("waypoints", [[0.0, 0.0], [300.0, 0.0], [600.0, 300.0]])

        imu_cfg = custom_config.get("imu", {})
        imu = IMUConfig(
            accelerometer_hz=float(imu_cfg.get("accelerometer_hz", 100.0)),
            gyroscope_hz=float(imu_cfg.get("gyroscope_hz", 100.0)),
            accel_noise_std=float(imu_cfg.get("accel_noise_std", 0.05)),
            gyro_noise_std=float(imu_cfg.get("gyro_noise_std", 0.005)),
        )

        gnss_cfg = custom_config.get("gnss", {})
        outages_raw = gnss_cfg.get("outages", [])
        outages = [
            GNSSOutage(
                start_seconds=float(o.get("start_seconds", o.get("start", 0))),
                end_seconds=float(o.get("end_seconds", o.get("end", 0))),
            )
            for o in outages_raw
        ]
        gnss = GNSSConfig(
            frequency_hz=float(gnss_cfg.get("frequency_hz", 1.0)),
            position_noise_meters=float(gnss_cfg.get("position_noise_meters", 3.0)),
            outages=outages,
        )

        scenario = SimulationScenario(
            scenario_id=scenario_id,
            name=name,
            duration_seconds=duration,
            timestep_seconds=float(custom_config.get("timestep_seconds", 0.01)),
            seed=seed,
            movement_mode=MovementMode.WAYPOINT_ROUTE,
            initial_state=initial_state,
            waypoints=waypoints,
            imu=imu,
            gnss=gnss,
        )
    else:
        preset_id = data.get("preset_id") or data.get("scenario_id") or "flagship_gnss_outage"
        presets = get_preset_scenarios()
        scenario = presets.get(preset_id, presets["flagship_gnss_outage"])
        seed = data.get("seed", scenario.seed)
        duration = data.get("duration_seconds", scenario.duration_seconds)
        scenario.seed = seed
        scenario.duration_seconds = duration

    run_obj = SimulationRun.objects.create(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        seed=scenario.seed,
        duration_seconds=scenario.duration_seconds,
        status=SimulationRun.Status.CREATED,
        scenario_config=scenario.to_dict(),
    )

    return run_obj


def trigger_simulation_job_service(run_obj: SimulationRun, run_sync: bool = False) -> SimulationRun:
    run_obj.status = SimulationRun.Status.QUEUED
    run_obj.save(update_fields=["status"])

    if run_sync:
        # Run synchronously for direct test/offline execution
        run_simulation_job_task(str(run_obj.id))
        run_obj.refresh_from_db()
    else:
        # Queue via Celery task queue
        run_simulation_job_task.delay(str(run_obj.id))

    return run_obj
