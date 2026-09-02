from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class GroundTruthState:
    """
    Pristine physical ground truth state at a specific simulation timestep.
    Position is measured in local ENU (East-North-Up) meters relative to origin.
    Geographic coordinates (latitude, longitude, altitude) are computed deterministically.
    """

    timestamp: float  # Simulation time in seconds
    x: float  # East position (meters)
    y: float  # North position (meters)
    z: float  # Up position (meters)
    vx: float  # East velocity (m/s)
    vy: float  # North velocity (m/s)
    vz: float  # Up velocity (m/s)
    ax: float  # East acceleration (m/s²)
    ay: float  # North acceleration (m/s²)
    az: float  # Up acceleration (m/s²)
    roll: float  # Roll orientation angle (radians)
    pitch: float  # Pitch orientation angle (radians)
    yaw: float  # Yaw orientation angle (radians)
    heading_deg: float  # Heading angle in degrees true north (0 to 360)
    angular_velocity_rad_s: float  # Yaw rate (rad/s)
    latitude: float  # WGS-84 latitude (degrees)
    longitude: float  # WGS-84 longitude (degrees)
    altitude: float  # WGS-84 altitude (meters)

    @property
    def speed(self) -> float:
        """Returns scalar speed in m/s."""
        return (self.vx**2 + self.vy**2 + self.vz**2) ** 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "speed": self.speed,
            "vx": self.vx,
            "vy": self.vy,
            "heading_deg": self.heading_deg,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
        }
