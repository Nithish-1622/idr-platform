import math
from typing import Any, Dict, List

import numpy as np


class EvaluationEngine:
    """
    Evaluates IDR estimated navigation trajectories against ground truth state time-series.
    Calculates RMSE, Final Position Error (FPE), Maximum Error, Distance Traveled,
    and SIH Drift Percentage, as well as detailed GNSS Outage performance metrics.
    """

    def __init__(self, dt: float = 0.01):
        self.dt = dt

    def evaluate(
        self,
        ground_truth_states: List[Any],
        estimated_states: List[Dict[str, Any]],
        outages: List[Any] = None,
    ) -> Dict[str, Any]:
        if not ground_truth_states or not estimated_states:
            return {"error": "Empty trajectory data for evaluation"}

        min_len = min(len(ground_truth_states), len(estimated_states))

        gt_xy = np.array([[gt.x, gt.y] for gt in ground_truth_states[:min_len]])
        est_xy = np.array([[est.get("x", 0.0), est.get("y", 0.0)] for est in estimated_states[:min_len]])
        timestamps = np.array([gt.timestamp for gt in ground_truth_states[:min_len]])

        # 1. Pointwise position errors
        errors = np.linalg.norm(est_xy - gt_xy, axis=1)

        # 2. RMSE
        rmse = float(np.sqrt(np.mean(errors**2)))

        # 3. Final Position Error (FPE)
        fpe = float(errors[-1])

        # 4. Max Position Error
        max_error = float(np.max(errors))
        mean_error = float(np.mean(errors))

        # 5. Total distance traveled
        if len(gt_xy) > 1:
            diffs = np.diff(gt_xy, axis=0)
            distances = np.linalg.norm(diffs, axis=1)
            total_distance = float(np.sum(distances))
        else:
            total_distance = 0.0

        # 6. Drift Percentage calculation
        # Formula: (Final Position Error / Total Distance Traveled) * 100
        drift_pct = float((fpe / total_distance) * 100.0) if total_distance > 0 else 0.0

        # 7. GNSS Outage Evaluation
        outage_metrics = []
        if outages:
            for outage in outages:
                start_t = getattr(outage, "start_seconds", 0.0)
                end_t = getattr(outage, "end_seconds", 0.0)

                mask = (timestamps >= start_t) & (timestamps <= end_t)
                if np.any(mask):
                    outage_errors = errors[mask]
                    max_outage_err = float(np.max(outage_errors))
                    mean_outage_err = float(np.mean(outage_errors))
                    outage_duration = max(end_t - start_t, 1e-3)
                    drift_rate = (outage_errors[-1] - outage_errors[0]) / outage_duration

                    outage_metrics.append(
                        {
                            "start_seconds": start_t,
                            "end_seconds": end_t,
                            "duration_seconds": outage_duration,
                            "initial_error_m": float(outage_errors[0]),
                            "final_error_m": float(outage_errors[-1]),
                            "max_error_m": max_outage_err,
                            "mean_error_m": mean_outage_err,
                            "drift_rate_m_per_s": float(drift_rate),
                        }
                    )

        return {
            "metrics": {
                "travelled_distance_m": round(total_distance, 2),
                "rmse_position_m": round(rmse, 4),
                "mean_position_error_m": round(mean_error, 4),
                "final_position_error_m": round(fpe, 4),
                "max_position_error_m": round(max_error, 4),
                "drift_percentage": round(drift_pct, 4),
            },
            "gnss_outage_evaluations": outage_metrics,
            "sample_count": min_len,
        }
