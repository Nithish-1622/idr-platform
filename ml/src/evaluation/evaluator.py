import numpy as np
import pandas as pd

class DeadReckoningEvaluator:
    def __init__(self, dt: float = 0.1):
        """
        Args:
            dt: Time step in seconds. Default 0.1s for 10Hz data.
        """
        self.dt = dt
        
    def integrate_kinematics(self, velocity_kmh: np.ndarray, yaw_rate_deg_s: np.ndarray, initial_heading_deg: float = 0.0) -> np.ndarray:
        """
        Integrates Velocity and Yaw Rate into X, Y local coordinate paths.
        
        Args:
            velocity_kmh: 1D array of velocity in km/h.
            yaw_rate_deg_s: 1D array of yaw rate in deg/s.
            initial_heading_deg: The starting heading in degrees.
            
        Returns:
            trajectory: (N, 2) array of (X, Y) coordinates in meters.
        """
        # Convert units
        velocity_ms = velocity_kmh / 3.6
        yaw_rate_rad_s = np.deg2rad(yaw_rate_deg_s)
        
        N = len(velocity_ms)
        trajectory = np.zeros((N, 2))
        
        x, y = 0.0, 0.0
        
        # Convert GNSS Heading (0=North, 90=East, CW) to Math ENU (0=East, 90=North, CCW)
        math_heading_deg = (90 - initial_heading_deg) % 360
        heading_rad = np.deg2rad(math_heading_deg)
        
        for i in range(N):
            # Vehicle yaw rate is typically CW positive. 
            # So a positive yaw rate (Right turn) decreases the CCW Math heading.
            heading_rad -= yaw_rate_rad_s[i] * self.dt
            
            # Update positions (Euler integration)
            x += velocity_ms[i] * np.cos(heading_rad) * self.dt
            y += velocity_ms[i] * np.sin(heading_rad) * self.dt
            
            trajectory[i, 0] = x
            trajectory[i, 1] = y
            
        return trajectory
        
    def calculate_drift(self, pred_trajectory: np.ndarray, true_trajectory: np.ndarray) -> dict:
        """
        Calculates Final Positional Error (FPE) and Average Distance Error (ADE).
        
        Args:
            pred_trajectory: (N, 2)
            true_trajectory: (N, 2)
        """
        # Final Positional Error
        fpe = np.linalg.norm(pred_trajectory[-1] - true_trajectory[-1])
        
        # Average Distance Error (across all points)
        errors = np.linalg.norm(pred_trajectory - true_trajectory, axis=1)
        ade = np.mean(errors)
        
        # Total distance traveled (based on true trajectory)
        diffs = np.diff(true_trajectory, axis=0)
        total_distance = np.sum(np.linalg.norm(diffs, axis=1))
        
        drift_percentage = (fpe / total_distance) * 100 if total_distance > 0 else 0
        
        return {
            "FPE_meters": fpe,
            "ADE_meters": ade,
            "Total_Distance_meters": total_distance,
            "Drift_Percentage": drift_percentage
        }
