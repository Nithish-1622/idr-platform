import math
from typing import Any, Dict, Optional

import numpy as np

from simulation.disturbances.disturbances import DisturbanceEngine
from simulation.scenario.schema import IMUConfig
from simulation.trajectory.kinematics import GroundTruthState
from .base import BaseSensor


class IMUSensor(BaseSensor):
    """
    Simulates smartphone 6-DOF IMU sensor readings (Accelerometer + Gyroscope).
    Calculates rotation-invariant features required by ML dev1 (ACC_MAG, GYRO_MAG, DYN_ACC_MAG).
    """

    GRAVITY = 9.80665  # Standard gravity m/s²

    def __init__(self, config: IMUConfig, disturbance_engine: Optional[DisturbanceEngine] = None):
        super().__init__(frequency_hz=config.accelerometer_hz, disturbance_engine=disturbance_engine)
        self.config = config

    def generate_measurement(self, state: GroundTruthState, step_idx: int) -> Optional[Dict[str, Any]]:
        if not self.should_sample(state.timestamp):
            return None

        self.last_sampled_timestamp = state.timestamp

        # Base physical acceleration in body frame (with gravity added to Z)
        raw_accel = np.array([state.ax, state.ay, state.az + self.GRAVITY])
        raw_gyro = np.array([0.0, 0.0, state.angular_velocity_rad_s])

        # Apply disturbances (noise, bias, drift)
        accel = self.disturbance_engine.add_constant_bias(raw_accel, np.array(self.config.accel_bias))
        accel = self.disturbance_engine.add_gaussian_noise(accel, self.config.accel_noise_std)
        accel = self.disturbance_engine.add_random_walk_drift(
            accel, self.config.accel_drift_rate, self.sampling_interval, step_idx
        )

        gyro = self.disturbance_engine.add_constant_bias(raw_gyro, np.array(self.config.gyro_bias))
        gyro = self.disturbance_engine.add_gaussian_noise(gyro, self.config.gyro_noise_std)
        gyro = self.disturbance_engine.add_random_walk_drift(
            gyro, self.config.gyro_drift_rate, self.sampling_interval, step_idx
        )

        # Compute dev1 rotation-invariant features
        acc_mag = float(np.linalg.norm(accel))
        gyro_mag = float(np.linalg.norm(gyro))

        dyn_accel = accel - np.array([0.0, 0.0, self.GRAVITY])
        dyn_acc_mag = float(np.linalg.norm(dyn_accel))

        return {
            "timestamp": state.timestamp,
            "sensor": "IMU",
            "ax": float(accel[0]),
            "ay": float(accel[1]),
            "az": float(accel[2]),
            "gx": float(gyro[0]),
            "gy": float(gyro[1]),
            "gz": float(gyro[2]),
            "ACC_MAG": acc_mag,
            "GYRO_MAG": gyro_mag,
            "DYN_ACC_MAG": dyn_acc_mag,
        }
