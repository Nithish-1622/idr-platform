import math
from simulation.scenario.presets import get_preset_scenarios
from simulation.trajectory.coordinate import (
    ecef_to_enu,
    ecef_to_geodetic,
    enu_to_geodetic,
    geodetic_to_ecef,
)
from simulation.trajectory.generator import TrajectoryGenerator


def test_coordinate_transforms_roundtrip():
    lat0, lon0, alt0 = 11.0168, 76.9558, 400.0
    east, north, up = 100.0, -200.0, 10.0

    lat, lon, alt = enu_to_geodetic(east, north, up, lat0, lon0, alt0)
    X, Y, Z = geodetic_to_ecef(lat, lon, alt)
    e2, n2, u2 = ecef_to_enu(X, Y, Z, lat0, lon0, alt0)

    assert math.isclose(east, e2, abs_tol=1e-3)
    assert math.isclose(north, n2, abs_tol=1e-3)
    assert math.isclose(up, u2, abs_tol=1e-3)


def test_straight_trajectory_kinematics():
    presets = get_preset_scenarios()
    sc = presets["straight_walking"]
    gen = TrajectoryGenerator(sc)
    states = gen.generate()

    assert len(states) > 0
    # Verify non-zero velocity and positive x/y movement
    assert states[-1].x > 0 or states[-1].y > 0
    assert math.isclose(states[0].speed, 1.4, abs_tol=1e-2)
