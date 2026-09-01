import numpy as np
from src.evaluation.evaluator import DeadReckoningEvaluator

def test_integration_straight_line():
    evaluator = DeadReckoningEvaluator(dt=1.0) # 1 sec dt
    
    # Moving straight at 36 km/h (10 m/s) for 5 seconds
    vel = np.full(5, 36.0)
    yaw = np.zeros(5) # No yaw
    
    traj = evaluator.integrate_kinematics(vel, yaw, initial_heading_deg=0)
    
    assert traj.shape == (5, 2)
    # X should increase by 10 each step, Y should be 0
    np.testing.assert_almost_equal(traj[0], [10.0, 0.0])
    np.testing.assert_almost_equal(traj[-1], [50.0, 0.0])

def test_integration_turn():
    evaluator = DeadReckoningEvaluator(dt=1.0)
    
    vel = np.array([36.0, 36.0]) # 10 m/s
    yaw = np.array([90.0, 0.0])  # turn 90 deg left on step 1
    
    traj = evaluator.integrate_kinematics(vel, yaw, initial_heading_deg=0)
    
    # Step 1: Heading is now 90 deg. X = 0, Y = 10
    np.testing.assert_almost_equal(traj[0], [0.0, 10.0])
    # Step 2: Heading remains 90 deg. X = 0, Y = 20
    np.testing.assert_almost_equal(traj[1], [0.0, 20.0])
