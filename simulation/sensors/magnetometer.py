import math
from typing import Any, Dict, Optional

import numpy as np

from simulation.disturbances.disturbances import DisturbanceEngine
from simulation.scenario.schema import MagnetometerConfig
from simulation.trajectory.kinematics import GroundTruthState
from .base import BaseSensor


class MagnetometerSensor(BaseSensor):
    """Simulates 3-axis digital compass magnetometer reading in microteslas (uT)."""

    DEFAULT_EARTH_FIELD_UT = 45.0  # ~45 uT average Earth magnetic field

    def __init__(self, config: MagnetometerConfig, disturbance_engine: Optional[DisturbanceEngine] = None):
        super().__init__(frequency_hz=config.frequency_hz, disturbance_engine=disturbance_engine)
        self.config = config

    def generate_measurement(self, state: GroundTruthState, step_idx: int) -> Optional[Dict[str, Any]]:
        if not self.should_sample(state.timestamp):
            return None

        self.last_sampled_timestamp = state.timestamp

        heading_rad = math.radians(state.heading_deg + self.config.declination_deg)
        mx = self.DEFAULT_EARTH_FIELD_UT * math.cos(heading_rad)
        my = self.DEFAULT_EARTH_FIELD_UT * math.sin(heading_rad)
        mz = -25.0  # Vertical component

        raw_mag = np.array([mx, my, mz])
        noisy_mag = self.disturbance_engine.add_gaussian_noise(raw_mag, self.config.noise_std_uT)

        return {
            "timestamp": state.timestamp,
            "sensor": "MAGNETOMETER",
            "mx_uT": float(noisy_mag[0]),
            "my_uT": float(noisy_mag[1]),
            "mz_uT": float(noisy_mag[2]),
        }
