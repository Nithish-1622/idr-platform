from simulation.evaluation.evaluator import EvaluationEngine
from simulation.trajectory.kinematics import GroundTruthState


def test_evaluation_engine_metrics():
    evaluator = EvaluationEngine(dt=0.1)

    gt_states = [
        GroundTruthState(
            timestamp=0.0, x=0.0, y=0.0, z=0.0, vx=1.0, vy=0.0, vz=0.0, ax=0.0, ay=0.0, az=0.0,
            roll=0.0, pitch=0.0, yaw=0.0, heading_deg=0.0, angular_velocity_rad_s=0.0,
            latitude=11.0, longitude=76.0, altitude=400.0
        ),
        GroundTruthState(
            timestamp=1.0, x=100.0, y=0.0, z=0.0, vx=1.0, vy=0.0, vz=0.0, ax=0.0, ay=0.0, az=0.0,
            roll=0.0, pitch=0.0, yaw=0.0, heading_deg=0.0, angular_velocity_rad_s=0.0,
            latitude=11.0, longitude=76.0, altitude=400.0
        ),
    ]

    # Estimated offset by 10m at end
    est_states = [
        {"x": 0.0, "y": 0.0},
        {"x": 110.0, "y": 0.0},
    ]

    res = evaluator.evaluate(gt_states, est_states)
    metrics = res["metrics"]

    assert metrics["travelled_distance_m"] == 100.0
    assert metrics["final_position_error_m"] == 10.0
    assert metrics["drift_percentage"] == 10.0  # (10m / 100m) * 100 = 10%
