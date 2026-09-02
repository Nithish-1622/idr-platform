from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from simulation.disturbances.disturbances import DisturbanceEngine
from simulation.trajectory.kinematics import GroundTruthState


class BaseSensor(ABC):
    """Abstract base class for all simulated sensors."""

    def __init__(self, frequency_hz: float, disturbance_engine: Optional[DisturbanceEngine] = None):
        self.frequency_hz = frequency_hz
        self.sampling_interval = 1.0 / frequency_hz if frequency_hz > 0 else 0.01
        self.disturbance_engine = disturbance_engine or DisturbanceEngine()
        self.last_sampled_timestamp = -1.0

    def should_sample(self, timestamp: float) -> bool:
        """Determines if the sensor should emit a measurement at current timestamp."""
        if self.last_sampled_timestamp < 0.0:
            return True
        return (timestamp - self.last_sampled_timestamp) >= (self.sampling_interval - 1e-6)

    @abstractmethod
    def generate_measurement(self, state: GroundTruthState, step_idx: int) -> Optional[Dict[str, Any]]:
        """Generates a sensor measurement observation dictionary derived from ground truth state."""
        pass
