from typing import Any, Dict, Optional

import numpy as np

from simulation.disturbances.disturbances import DisturbanceEngine
from simulation.scenario.schema import GNSSConfig
from simulation.trajectory.kinematics import GroundTruthState
from .base import BaseSensor


class GNSSSensor(BaseSensor):
    """
    Simulates GNSS satellite receiver observations.
    Evaluates outage intervals; suppresses GNSS telemetry emission during outages.
    """

    def __init__(self, config: GNSSConfig, disturbance_engine: Optional[DisturbanceEngine] = None):
        super().__init__(frequency_hz=config.frequency_hz, disturbance_engine=disturbance_engine)
        self.config = config

    def is_in_outage(self, timestamp: float) -> bool:
        """Returns True if the timestamp falls inside any configured GNSS outage window."""
        for outage in self.config.outages:
            if outage.start_seconds <= timestamp <= outage.end_seconds:
                return True
        return False

    def generate_measurement(self, state: GroundTruthState, step_idx: int) -> Optional[Dict[str, Any]]:
        if not self.should_sample(state.timestamp):
            return None

        self.last_sampled_timestamp = state.timestamp

        # Check outage condition
        if self.is_in_outage(state.timestamp):
            return {
                "timestamp": state.timestamp,
                "sensor": "GNSS",
                "status": "UNAVAILABLE",
                "latitude": None,
                "longitude": None,
                "altitude": None,
                "speed_mps": None,
                "heading_deg": None,
            }

        # Apply position noise
        noise_xy = self.disturbance_engine.add_gaussian_noise(
            np.zeros(2), self.config.position_noise_meters
        )
        noise_z = self.disturbance_engine.add_gaussian_noise(
            np.zeros(1), self.config.altitude_noise_meters
        )[0]

        # Convert ENU noise offset to lat/lon meters approx
        lat_offset_deg = noise_xy[1] / 111139.0
        lon_offset_deg = noise_xy[0] / (111139.0 * np.cos(np.radians(state.latitude)))

        return {
            "timestamp": state.timestamp,
            "sensor": "GNSS",
            "status": "AVAILABLE",
            "latitude": float(state.latitude + lat_offset_deg),
            "longitude": float(state.longitude + lon_offset_deg),
            "altitude": float(state.altitude + noise_z),
            "speed_mps": float(state.speed),
            "heading_deg": float(state.heading_deg),
        }
