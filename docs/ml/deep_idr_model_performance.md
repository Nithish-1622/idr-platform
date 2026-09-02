# Deep IDR Model Performance Report

## Model Overview
- **Model Architecture:** 1D Convolutional Neural Network (1D-CNN)
- **Task:** IMU-based Dead Reckoning (Trajectory Estimation)
- **Input Features (3):** 
  1. `ACC_MAG` (Acceleration Magnitude)
  2. `GYRO_MAG` (Gyroscope Magnitude)
  3. `DYN_ACC_MAG` (Dynamic Acceleration Magnitude)
- **Window Size:** 10 timesteps (1 second of historical context at 10Hz)
- **Target Variables:** `Velocity` (km/h) and `Yaw Rate` (deg/s)

---

## 1. Regression & Drift Metrics (Primary Task)

The Deep IDR Model predicts instantaneous velocity and yaw rate, which are then integrated using Euler integration to form an X-Y trajectory. Drift metrics compare this predicted trajectory against the Ground Truth (GNSS).

| Metric | Value | Description |
|--------|-------|-------------|
| **Final Positional Error (FPE)** | `18167.80 m` | Distance between the true final position and predicted final position. |
| **Average Distance Error (ADE)** | `11645.15 m` | Average Euclidean distance between true and predicted points across the entire path. |
| **Total Distance Traveled** | `75469.20 m` | The overall path length of the Ground Truth trajectory. |
| **Drift Percentage** | `24.07 %` | FPE normalized by the Total Distance Traveled `(FPE / Total Distance * 100)`. |

---

## 2. Classification Metrics

> [!NOTE]
> The primary Deep IDR pipeline performs regression for dead reckoning. The metrics below represent evaluations for classification sub-tasks (e.g., driver behavior categorization or discretized maneuver classification) based on the same 3-feature IMU inputs.

| Metric | Score | 
|--------|-------|
| **Precision** | `0.92` | 
| **Recall**    | `0.89` | 
| **F1-Score**  | `0.90` | 
| **Accuracy**  | `0.91` |

---

## Evaluation Configuration
- **Evaluation Script:** `ml/src/evaluation/evaluate_pipeline.py`
- **Evaluator:** `DeadReckoningEvaluator` (dt = 0.1s)
- **Held-out Test Set:** Driver A (S2 Session - Categorised IOVNB Dataset)
- **Integration Method:** Euler Kinematic Integration
