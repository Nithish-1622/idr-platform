from typing import Tuple
from .schema import MovementMode, SimulationScenario


class ScenarioValidationError(ValueError):
    """Raised when a SimulationScenario contains invalid or unphysical configurations."""
    pass


def validate_scenario(scenario: SimulationScenario) -> Tuple[bool, str]:
    """
    Validates scenario parameters.
    Returns (True, "OK") if valid, otherwise raises ScenarioValidationError.
    """
    if scenario.duration_seconds <= 0:
        raise ScenarioValidationError("duration_seconds must be positive.")

    if scenario.timestep_seconds <= 0:
        raise ScenarioValidationError("timestep_seconds must be positive.")

    if scenario.timestep_seconds > scenario.duration_seconds:
        raise ScenarioValidationError("timestep_seconds cannot be larger than duration_seconds.")

    if scenario.imu.accelerometer_hz <= 0 or scenario.imu.gyroscope_hz <= 0:
        raise ScenarioValidationError("IMU sampling frequencies must be positive.")

    if scenario.gnss.frequency_hz <= 0:
        raise ScenarioValidationError("GNSS frequency must be positive.")

    for outage in scenario.gnss.outages:
        if outage.start_seconds < 0 or outage.end_seconds < 0:
            raise ScenarioValidationError("GNSS outage timestamps cannot be negative.")
        if outage.start_seconds >= outage.end_seconds:
            raise ScenarioValidationError("GNSS outage start must be less than end timestamp.")
        if outage.end_seconds > scenario.duration_seconds:
            raise ScenarioValidationError("GNSS outage end timestamp exceeds scenario duration.")

    if scenario.movement_mode == MovementMode.WAYPOINT_ROUTE and not scenario.waypoints:
        # Default fallback route if empty
        scenario.waypoints = [[0.0, 0.0], [100.0, 0.0], [100.0, 200.0], [300.0, 200.0]]

    return True, "OK"
