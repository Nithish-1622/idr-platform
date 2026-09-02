import logging
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from ml.src.evaluation.evaluator import DeadReckoningEvaluator
from .base import BaseIDRAdapter

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_ONNX_PATH = BASE_DIR / "ml" / "models" / "deploy" / "deep_idr.onnx"


class PerfectGroundTruthAdapter(BaseIDRAdapter):
    """Reference adapter returning perfect ground truth states for baseline testing."""

    def __init__(self, ground_truth_states: List[Any]):
        self.ground_truth_states = ground_truth_states

    def process_stream(self, sensor_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        estimated = []
        for gt in self.ground_truth_states:
            estimated.append(
                {
                    "timestamp": gt.timestamp,
                    "x": gt.x,
                    "y": gt.y,
                    "z": gt.z,
                    "velocity": gt.speed,
                    "heading": gt.heading_deg,
                    "confidence": 1.0,
                    "navigation_mode": "PERFECT_GROUND_TRUTH",
                }
            )
        return estimated


class ReferenceONNXIDRAdapter(BaseIDRAdapter):
    """
    Adapter that executes ML dev1's trained deep_idr.onnx neural network model
    on the simulated IMU sensor stream and integrates predicted kinematics into 2D ENU position coordinates.
    """

    def __init__(self, onnx_model_path: Path = None, dt: float = 0.1, window_size: int = 10):
        self.model_path = onnx_model_path or DEFAULT_ONNX_PATH
        self.dt = dt
        self.window_size = window_size
        self.session = None

        if self.model_path.exists():
            try:
                import onnxruntime as ort

                self.session = ort.InferenceSession(str(self.model_path))
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
            except Exception as e:
                logger.warning("Failed to initialize ONNX runtime session: %s", e)

        self.evaluator = DeadReckoningEvaluator(dt=self.dt)

    def process_stream(self, sensor_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Filter IMU records
        imu_records = [r for r in sensor_records if r.get("sensor") == "IMU"]
        if not imu_records:
            return []

        # Extract features: [ACC_MAG, GYRO_MAG, DYN_ACC_MAG]
        features_list = []
        timestamps = []
        for r in imu_records:
            acc_mag = r.get("ACC_MAG", 9.80665)
            gyro_mag = r.get("GYRO_MAG", 0.0)
            dyn_acc_mag = r.get("DYN_ACC_MAG", 0.0)
            features_list.append([acc_mag, gyro_mag, dyn_acc_mag])
            timestamps.append(r.get("timestamp", 0.0))

        feat_arr = np.array(features_list, dtype=np.float32)
        N = len(feat_arr)

        if N < self.window_size:
            # Pad sequence if smaller than window size
            padding = np.tile(feat_arr[0], (self.window_size - N, 1))
            feat_arr = np.vstack([padding, feat_arr])
            N = len(feat_arr)

        # Sliding window inference
        velocities_ms = []
        yaw_rates_rad_s = []

        num_windows = N - self.window_size + 1
        for i in range(num_windows):
            window = feat_arr[i : i + self.window_size, :]  # Shape: (10, 3)
            tensor_input = np.expand_dims(window, axis=0)  # Shape: (1, 10, 3)

            if self.session is not None:
                outputs = self.session.run([self.output_name], {self.input_name: tensor_input})
                pred = outputs[0][0]  # [velocity_ms, yaw_rate_rad_s]
                vel_ms = float(pred[0])
                yaw_rate = float(pred[1])
            else:
                # Stub mathematical approximation fallback if ONNX fails
                vel_ms = float(np.mean(window[:, 0])) * 0.1
                yaw_rate = float(np.mean(window[:, 1]))

            velocities_ms.append(vel_ms)
            yaw_rates_rad_s.append(yaw_rate)

        # Integrate kinematics into 2D ENU positions
        velocities_kmh = np.array(velocities_ms) * 3.6
        yaw_rates_deg_s = np.rad2deg(np.array(yaw_rates_rad_s))

        trajectory_xy = self.evaluator.integrate_kinematics(
            velocity_kmh=velocities_kmh, yaw_rate_deg_s=yaw_rates_deg_s, initial_heading_deg=0.0
        )

        estimated = []
        for idx in range(len(trajectory_xy)):
            t_idx = min(idx + self.window_size - 1, len(timestamps) - 1)
            estimated.append(
                {
                    "timestamp": timestamps[t_idx] if timestamps else idx * self.dt,
                    "x": float(trajectory_xy[idx, 0]),
                    "y": float(trajectory_xy[idx, 1]),
                    "z": 0.0,
                    "velocity": float(velocities_ms[idx]),
                    "heading": float((math.degrees(np.arctan2(trajectory_xy[idx, 0], trajectory_xy[idx, 1]))) % 360),
                    "confidence": 0.95,
                    "navigation_mode": "AI_IDR_ONNX",
                }
            )

        return estimated
