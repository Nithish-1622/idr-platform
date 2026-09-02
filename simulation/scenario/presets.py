from typing import Dict
from .schema import (
    DisturbanceConfig,
    GNSSConfig,
    GNSSOutage,
    IMUConfig,
    InitialState,
    MagnetometerConfig,
    MovementMode,
    SimulationScenario,
)


def get_preset_scenarios() -> Dict[str, SimulationScenario]:
    """Returns a registry of standard pre-configured deterministic simulation scenarios."""
    scenarios = {}

    # 1. Static Device
    scenarios["static_device"] = SimulationScenario(
        scenario_id="static_device",
        name="Static Device Test",
        description="Stationary device on flat surface to baseline noise floor",
        duration_seconds=60.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.CONSTANT_VELOCITY,
        initial_state=InitialState(velocity_mps=0.0, heading_deg=0.0),
    )

    # 2. Straight Walking
    scenarios["straight_walking"] = SimulationScenario(
        scenario_id="straight_walking",
        name="Straight Line Walking",
        description="Constant 1.4 m/s pedestrian movement in straight line",
        duration_seconds=120.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.STRAIGHT,
        initial_state=InitialState(velocity_mps=1.4, heading_deg=90.0),
    )

    # 3. Constant Speed Walking
    scenarios["constant_speed_walking"] = SimulationScenario(
        scenario_id="constant_speed_walking",
        name="Constant Speed Walking",
        description="Uniform velocity 1.5 m/s",
        duration_seconds=180.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.CONSTANT_VELOCITY,
        initial_state=InitialState(velocity_mps=1.5, heading_deg=45.0),
    )

    # 4. Stop and Go Walking
    scenarios["stop_and_go_walking"] = SimulationScenario(
        scenario_id="stop_and_go_walking",
        name="Stop and Go Walking",
        description="Pedestrian with periodic acceleration and 5-second stops",
        duration_seconds=150.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.STOP_AND_GO,
        initial_state=InitialState(velocity_mps=1.2, heading_deg=0.0),
    )

    # 5. Turning Route
    scenarios["turning_route"] = SimulationScenario(
        scenario_id="turning_route",
        name="90-Degree Turning Route",
        description="City block navigation with 90-degree left and right turns",
        duration_seconds=200.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.TURN,
        initial_state=InitialState(velocity_mps=2.0, heading_deg=0.0),
        waypoints=[[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0], [0.0, 0.0]],
    )

    # 6. Vehicle Route
    scenarios["vehicle_route"] = SimulationScenario(
        scenario_id="vehicle_route",
        name="High-Speed Vehicle Route",
        description="Vehicle traveling at 12 m/s (~43 km/h) through urban grid",
        duration_seconds=300.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(velocity_mps=12.0, heading_deg=0.0),
        waypoints=[[0.0, 0.0], [500.0, 0.0], [500.0, 800.0], [1200.0, 800.0]],
    )

    # 7. GNSS Outage Scenario
    scenarios["gnss_outage"] = SimulationScenario(
        scenario_id="gnss_outage",
        name="Urban Tunnel GNSS Outage",
        description="60-second complete GNSS loss during tunnel traversal",
        duration_seconds=180.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(velocity_mps=10.0, heading_deg=90.0),
        waypoints=[[0.0, 0.0], [400.0, 0.0], [800.0, 200.0]],
        gnss=GNSSConfig(
            frequency_hz=1.0,
            position_noise_meters=3.0,
            outages=[GNSSOutage(start_seconds=60.0, end_seconds=120.0)],
        ),
    )

    # 8. GNSS Degraded
    scenarios["gnss_degraded"] = SimulationScenario(
        scenario_id="gnss_degraded",
        name="Urban Canyon Degraded GNSS",
        description="High multipath environment with 15m GNSS position noise",
        duration_seconds=180.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=15.0),
    )

    # 9. High IMU Noise
    scenarios["high_imu_noise"] = SimulationScenario(
        scenario_id="high_imu_noise",
        name="High Noise Low-Cost Consumer IMU",
        description="Severe MEMS accelerometer and gyroscope noise",
        duration_seconds=120.0,
        timestep_seconds=0.01,
        seed=42,
        imu=IMUConfig(accel_noise_std=0.25, gyro_noise_std=0.03),
    )

    # 10. High IMU Bias
    scenarios["high_imu_bias"] = SimulationScenario(
        scenario_id="high_imu_bias",
        name="High Temperature IMU Bias Drift",
        description="Large uncalibrated accelerometer and gyroscope bias",
        duration_seconds=120.0,
        timestep_seconds=0.01,
        seed=42,
        imu=IMUConfig(
            accel_bias=[0.15, -0.10, 0.20],
            gyro_bias=[0.01, -0.015, 0.02],
            accel_drift_rate=0.001,
            gyro_drift_rate=0.0005,
        ),
    )

    # 11. FLAGSHIP SIH DEMONSTRATION SCENARIO
    scenarios["flagship_gnss_outage"] = SimulationScenario(
        scenario_id="flagship_gnss_outage",
        name="SIH-2026 Flagship 300s GNSS Outage Benchmark",
        description=(
            "Flagship 300-second navigation benchmark with 120-second middle GNSS outage "
            "(t=120s to t=240s) for testing dead reckoning position drift and recovery."
        ),
        duration_seconds=300.0,
        timestep_seconds=0.01,
        seed=42,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(
            latitude=11.0168,
            longitude=76.9558,
            altitude=400.0,
            velocity_mps=8.0,
            heading_deg=90.0,
        ),
        waypoints=[
            [0.0, 0.0],
            [300.0, 0.0],
            [600.0, 300.0],
            [600.0, 800.0],
            [1000.0, 800.0],
        ],
        imu=IMUConfig(
            accelerometer_hz=100.0,
            gyroscope_hz=100.0,
            accel_noise_std=0.05,
            gyro_noise_std=0.005,
            accel_bias=[0.01, -0.01, 0.02],
            gyro_bias=[0.001, -0.001, 0.002],
        ),
        gnss=GNSSConfig(
            frequency_hz=1.0,
            position_noise_meters=3.0,
            altitude_noise_meters=5.0,
            outages=[GNSSOutage(start_seconds=120.0, end_seconds=240.0)],
        ),
        magnetometer=MagnetometerConfig(frequency_hz=50.0, noise_std_uT=0.5),
        disturbances=DisturbanceConfig(scale_factor_error_pct=0.01),
    )

    # 12. Urban Tunnel GNSS Outage Scenario (Real-World City Center)
    scenarios["urban_tunnel_outage"] = SimulationScenario(
        scenario_id="urban_tunnel_outage",
        name="Urban Tunnel GNSS Outage",
        description="City center route entering a 120s subterranean tunnel with total GNSS signal loss",
        duration_seconds=250.0,
        timestep_seconds=0.01,
        seed=101,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(latitude=28.6139, longitude=77.2090, velocity_mps=11.1, heading_deg=45.0),
        waypoints=[[0, 0], [250, 250], [600, 250], [900, 500]],
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=2.5, outages=[GNSSOutage(start_seconds=50.0, end_seconds=170.0)]),
    )

    # 13. High-Speed Highway Corridor
    scenarios["highway_corridor"] = SimulationScenario(
        scenario_id="highway_corridor",
        name="High-Speed Highway Corridor",
        description="Suburban expressway navigation at 25 m/s (~90 km/h) testing long-range IMU velocity integration",
        duration_seconds=300.0,
        timestep_seconds=0.01,
        seed=202,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(latitude=19.0760, longitude=72.8777, velocity_mps=25.0, heading_deg=90.0),
        waypoints=[[0, 0], [1500, 0], [3500, 500], [6000, 500]],
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=4.0),
    )

    # 14. Urban Canyon Multipath Degradation
    scenarios["urban_canyon_degraded"] = SimulationScenario(
        scenario_id="urban_canyon_degraded",
        name="Urban Canyon Multipath Degradation",
        description="High-rise building district creating severe satellite multipath reflection and 15m position jitter",
        duration_seconds=200.0,
        timestep_seconds=0.01,
        seed=303,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(latitude=12.9716, longitude=77.5946, velocity_mps=5.0, heading_deg=0.0),
        waypoints=[[0, 0], [0, 300], [200, 300], [200, 600]],
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=15.0),
    )

    # 15. Subway & Underground Transit Transfer
    scenarios["subway_transfer"] = SimulationScenario(
        scenario_id="subway_transfer",
        name="Subway & Underground Transit Transfer",
        description="Pedestrian descending into metro station concourse with 90s complete blackout",
        duration_seconds=180.0,
        timestep_seconds=0.01,
        seed=404,
        movement_mode=MovementMode.STOP_AND_GO,
        initial_state=InitialState(latitude=13.0827, longitude=80.2707, velocity_mps=1.3, heading_deg=180.0),
        waypoints=[[0, 0], [0, -100], [-50, -100], [-50, -200]],
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=3.0, outages=[GNSSOutage(start_seconds=30.0, end_seconds=120.0)]),
    )

    # 16. Mountain Winding Road & Pass
    scenarios["mountain_winding_road"] = SimulationScenario(
        scenario_id="mountain_winding_road",
        name="Mountain Winding Road & Pass",
        description="Serpentine mountain highway with continuous sharp turns and periodic hill shading",
        duration_seconds=240.0,
        timestep_seconds=0.01,
        seed=505,
        movement_mode=MovementMode.WAYPOINT_ROUTE,
        initial_state=InitialState(latitude=32.2432, longitude=77.1892, velocity_mps=8.5, heading_deg=45.0),
        waypoints=[[0, 0], [150, 100], [100, 300], [300, 450], [200, 700]],
        gnss=GNSSConfig(frequency_hz=1.0, position_noise_meters=5.0, outages=[GNSSOutage(start_seconds=80.0, end_seconds=140.0)]),
    )

    return scenarios
