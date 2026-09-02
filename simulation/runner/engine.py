import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from simulation.adapters.base import BaseIDRAdapter
from simulation.adapters.idr_adapter import ReferenceONNXIDRAdapter
from simulation.disturbances.disturbances import DisturbanceEngine
from simulation.evaluation.evaluator import EvaluationEngine
from simulation.exporters.csv_exporter import CSVExporter
from simulation.exporters.json_exporter import JSONExporter
from simulation.scenario.schema import SimulationScenario
from simulation.scenario.validator import validate_scenario
from simulation.sensors.gnss import GNSSSensor
from simulation.sensors.imu import IMUSensor
from simulation.sensors.magnetometer import MagnetometerSensor
from simulation.trajectory.generator import TrajectoryGenerator

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Main deterministic simulation runner.
    Generates ground truth, simulates sensor streams with disturbances, evaluates IDR estimates,
    and produces structured simulation results and export artifacts.
    """

    def __init__(self, scenario: SimulationScenario, idr_adapter: Optional[BaseIDRAdapter] = None):
        validate_scenario(scenario)
        self.scenario = scenario
        self.dt = scenario.timestep_seconds

        # Seed disturbance engine for reproducible randomness
        self.disturbance_engine = DisturbanceEngine(seed=scenario.seed)

        # Sensors
        self.imu_sensor = IMUSensor(scenario.imu, disturbance_engine=self.disturbance_engine)
        self.gnss_sensor = GNSSSensor(scenario.gnss, disturbance_engine=self.disturbance_engine)
        self.mag_sensor = (
            MagnetometerSensor(scenario.magnetometer, disturbance_engine=self.disturbance_engine)
            if scenario.magnetometer
            else None
        )

        # Evaluator and Adapter
        self.evaluator = EvaluationEngine(dt=self.dt)
        self.idr_adapter = idr_adapter or ReferenceONNXIDRAdapter(dt=self.dt)

    def run(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Runs the simulation completely in-memory in fast, controlled timesteps."""
        logger.info("Starting simulation run for scenario '%s' (seed=%d)...", self.scenario.scenario_id, self.scenario.seed)

        # 1. Generate Ground Truth
        traj_gen = TrajectoryGenerator(self.scenario)
        ground_truth_states = traj_gen.generate()

        # 2. Simulate Sensor Observations
        sensor_records: List[Dict[str, Any]] = []

        for step_idx, state in enumerate(ground_truth_states):
            imu_msg = self.imu_sensor.generate_measurement(state, step_idx)
            if imu_msg:
                sensor_records.append(imu_msg)

            gnss_msg = self.gnss_sensor.generate_measurement(state, step_idx)
            if gnss_msg:
                sensor_records.append(gnss_msg)

            if self.mag_sensor:
                mag_msg = self.mag_sensor.generate_measurement(state, step_idx)
                if mag_msg:
                    sensor_records.append(mag_msg)

        # 3. Execute IDR Adapter Evaluation
        estimated_states = self.idr_adapter.process_stream(sensor_records)

        # 4. Compute Evaluation Metrics
        eval_result = self.evaluator.evaluate(
            ground_truth_states=ground_truth_states,
            estimated_states=estimated_states,
            outages=self.scenario.gnss.outages,
        )

        # Build structured result payload
        result_payload = {
            "simulator_version": "1.0.0",
            "scenario_id": self.scenario.scenario_id,
            "scenario_name": self.scenario.name,
            "seed": self.scenario.seed,
            "duration_seconds": self.scenario.duration_seconds,
            "sample_counts": {
                "ground_truth_frames": len(ground_truth_states),
                "sensor_observation_records": len(sensor_records),
                "estimated_frames": len(estimated_states),
            },
            "metrics": eval_result.get("metrics", {}),
            "gnss_outage_evaluations": eval_result.get("gnss_outage_evaluations", []),
        }

        # 5. Persist Export Artifacts if output_dir provided
        artifacts = {}
        if output_dir:
            out_path = Path(output_dir)
            gt_path = CSVExporter.export_ground_truth(ground_truth_states, out_path / "ground_truth.csv")
            sensor_path = CSVExporter.export_sensor_stream(sensor_records, out_path / "sensor_stream.csv")
            report_path = JSONExporter.export_report(result_payload, out_path / "evaluation_report.json")

            artifacts = {
                "ground_truth_csv": str(gt_path),
                "sensor_stream_csv": str(sensor_path),
                "evaluation_report_json": str(report_path),
            }

        result_payload["artifacts"] = artifacts
        logger.info("Simulation run for '%s' completed successfully.", self.scenario.scenario_id)

        return {
            "result": result_payload,
            "ground_truth_states": ground_truth_states,
            "sensor_records": sensor_records,
            "estimated_states": estimated_states,
        }
