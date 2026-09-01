# Phase 1: IO-VNBD Dataset Report

## Dataset Location
The local dataset is located at `ml/data/`.
Specifically, we explored the subsets:
- `ml/data/Synchronised V abd S datasets/`
- `ml/data/Unsynchronised V and S Dataset/`

## Files and Formats
The data is predominantly stored in **CSV** format, with some supplementary image files (.JPG). The dataset is categorized by different drivers and vehicles (e.g., Driver A, B, D, E).
- **S-*.csv**: Smartphone data
- **V-*.csv**: Vehicle data

## Sensors
**Smartphone Sensors (`S-*.csv`):**
- GPS (Latitude, Longitude, Altitude, Speed, Accuracy, Orientation)
- Accelerometer (X, Y, Z in m/s²)
- Gravity (X, Y, Z in m/s²)
- Gyroscope (Yaw, Pitch, Roll in rad/s)
- Magnetic Field (X, Y, Z in μT)
- Orientation (Yaw, Pitch, Roll in degrees)

**Vehicle Sensors (`V-*.csv`):**
- GPS (Latitude, Longitude, Height, Velocity, Heading)
- Wheel Speeds (Front Left, Front Right, Rear Left, Rear Right in rad/sec)
- Yaw Rate (deg/sec)
- Indicated Vehicle Speed (km/hr)
- Indicated Longitudinal/Lateral Acceleration (g)
- Steering Angle (degrees)
- OBD/CAN signals (Gear, Engine Speed, Brake Pressure, etc.)

## Sampling Rates
Based on timestamps from both smartphone and vehicle data streams, the sampling interval is **0.1 seconds (10 Hz)**.

## Timestamp Information
- Smartphone: `TIME SINCE START (ms)` and formatted `DATE (YYYY-MO-DD HH-MI-SS_SSS)`.
- Vehicle: `Time Since Start of Day (seconds)` and `Sample period (seconds)`.
The Synchronised dataset has perfectly matching row counts (e.g., 105,974 rows) for corresponding S and V files.

## Available Reference / Ground Truth
The vehicle dataset provides high-quality reference signals directly from the car's internal sensors:
- Actual Vehicle Velocity (`Velocity (km/hr)`)
- Actual Yaw Rate
- Steering Angle
- High-quality Vehicle GPS (Lat/Long/Heading)

## Missing Data
A preliminary scan of the `M (Driver B)` synchronised subset shows **0 null values (NaN)** in the CSVs. However, broader checks across all drivers may reveal gaps, and GNSS satellite drops may present as implicit missing/degraded data.

## Potential Targets
Instead of directly predicting Lat/Long (which is difficult for an IMU over long periods), the ML model should predict intermediate kinematics which the navigation engine will integrate:
1. **Vehicle Velocity** (Forward motion)
2. **Vehicle Yaw Rate** (Turning motion)
3. **Velocity/Heading Error Bias**

## Potential Model Inputs
From the smartphone data (during GPS outage):
- Accelerometer (X, Y, Z)
- Gyroscope (Yaw, Pitch, Roll)
- Gravity vector (to determine phone mounting orientation)
- Rolling window features (mean, variance) of the IMU data

## Potential Limitations
1. **Mounting Orientation**: The smartphone may be mounted differently in each car. The model must learn rotation-invariant features or we must use gravity vectors to align the IMU frame to the vehicle frame before inference.
2. **Synchronisation quality**: Although the 'Synchronised' folder exists, hardware-level timestamp offsets between the phone IMU and car OBD might still be present.
3. **Generalization**: Model might overfit to specific drivers' driving styles if not carefully cross-validated.
