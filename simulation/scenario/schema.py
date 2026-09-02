from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class MovementMode(str, Enum):
    STRAIGHT = "STRAIGHT"
    CONSTANT_VELOCITY = "CONSTANT_VELOCITY"
    ACCELERATION = "ACCELERATION"
    DECELERATION = "DECELERATION"
    STOP_AND_GO = "STOP_AND_GO"
    CIRCULAR = "CIRCULAR"
    TURN = "TURN"
    WAYPOINT_ROUTE = "WAYPOINT_ROUTE"


@dataclass
class InitialState:
    latitude: float = 11.0168
    longitude: float = 76.9558
    altitude: float = 400.0
    velocity_mps: float = 0.0
    heading_deg: float = 0.0


@dataclass
class IMUConfig:
    accelerometer_hz: float = 100.0
    gyroscope_hz: float = 100.0
    accel_noise_std: float = 0.05
    gyro_noise_std: float = 0.005
    accel_bias: List[float] = field(default_factory=lambda: [0.01, -0.01, 0.02])
    gyro_bias: List[float] = field(default_factory=lambda: [0.001, -0.001, 0.002])
    accel_drift_rate: float = 0.0001
    gyro_drift_rate: float = 0.00005


@dataclass
class GNSSOutage:
    start_seconds: float
    end_seconds: float


@dataclass
class GNSSConfig:
    frequency_hz: float = 1.0
    position_noise_meters: float = 3.0
    altitude_noise_meters: float = 5.0
    outages: List[GNSSOutage] = field(default_factory=list)


@dataclass
class MagnetometerConfig:
    frequency_hz: float = 50.0
    noise_std_uT: float = 0.5
    declination_deg: float = -1.2


@dataclass
class DisturbanceConfig:
    dropout_probability: float = 0.0
    scale_factor_error_pct: float = 0.0
    outlier_probability: float = 0.0
    outlier_scale: float = 5.0


@dataclass
class SimulationScenario:
    scenario_id: str
    name: str
    description: str = ""
    duration_seconds: float = 300.0
    timestep_seconds: float = 0.01
    seed: int = 42
    movement_mode: MovementMode = MovementMode.WAYPOINT_ROUTE
    initial_state: InitialState = field(default_factory=InitialState)
    waypoints: List[List[float]] = field(default_factory=list)
    imu: IMUConfig = field(default_factory=IMUConfig)
    gnss: GNSSConfig = field(default_factory=GNSSConfig)
    magnetometer: Optional[MagnetometerConfig] = field(default_factory=MagnetometerConfig)
    disturbances: DisturbanceConfig = field(default_factory=DisturbanceConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "timestep_seconds": self.timestep_seconds,
            "seed": self.seed,
            "movement_mode": self.movement_mode.value,
            "initial_state": {
                "latitude": self.initial_state.latitude,
                "longitude": self.initial_state.longitude,
                "altitude": self.initial_state.altitude,
                "velocity_mps": self.initial_state.velocity_mps,
                "heading_deg": self.initial_state.heading_deg,
            },
            "waypoints": self.waypoints,
            "imu": {
                "accelerometer_hz": self.imu.accelerometer_hz,
                "gyroscope_hz": self.imu.gyroscope_hz,
                "accel_noise_std": self.imu.accel_noise_std,
                "gyro_noise_std": self.imu.gyro_noise_std,
                "accel_bias": self.imu.accel_bias,
                "gyro_bias": self.imu.gyro_bias,
            },
            "gnss": {
                "frequency_hz": self.gnss.frequency_hz,
                "position_noise_meters": self.gnss.position_noise_meters,
                "outages": [
                    {"start_seconds": o.start_seconds, "end_seconds": o.end_seconds}
                    for o in self.gnss.outages
                ],
            },
        }
