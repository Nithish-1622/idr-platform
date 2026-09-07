# Deep IDR Model Architecture and Pipeline

This document provides a comprehensive overview of the Deep Inertial Dead Reckoning (Deep IDR) machine learning model, detailing its architecture, the data processing pipeline, and the training methodology.

## 1. Overview

The Deep IDR model is designed to predict a vehicle's motion (velocity and yaw rate) purely from smartphone sensor data (Accelerometer and Gyroscope) without relying on GNSS (GPS) signals. This enables highly accurate dead-reckoning during GPS-denied scenarios (e.g., tunnels, urban canyons).

The model achieves exceptional generalization across different drivers, vehicles, and sensor mounting positions by employing a strictly **rotation-invariant feature engineering** approach.

---

## 2. Data Processing Pipeline

The machine learning pipeline processes raw, uncalibrated smartphone sensor data into normalized features suitable for the neural network.

### Step 2.1: Data Cleaning (`cleaner.py`)
- **Resampling:** Raw sensor data (often arriving at irregular intervals like 100Hz or 50Hz) is interpolated to a strict **10 Hz** frequency.
- **GNSS Target Derivation:** Ground truth targets are derived from the GNSS data.
  - **Velocity:** Directly extracted from the GNSS speed.
  - **Yaw Rate (Heading Rate):** Calculated by taking the derivative of the GNSS Heading over time. Strict angle unwrapping is applied to handle the 360° to 0° rollover, ensuring continuous mathematical derivatives.

### Step 2.2: Synchronization (`sync.py`)
- Smartphone sensors and GNSS receivers operate on independent hardware clocks.
- The pipeline uses a normalized cross-correlation algorithm on the magnitude of dynamic acceleration versus GNSS speed changes to mathematically synchronize the temporal offset between the two streams.
- Any dataset that fails to correlate mathematically (e.g., corrupted sensor data) is automatically flagged and rejected.

### Step 2.3: Gravity Alignment (`aligner.py`)
- **Rotation-Invariance:** Because a smartphone can be mounted in any orientation (landscape, portrait, tilted), raw X/Y/Z axes are useless.
- The pipeline estimates the Gravity Vector using a low-pass filter on the raw accelerometer.
- By projecting the Gyroscope readings onto this estimated gravity vector, we isolate the true **Yaw Rate (Z-axis rotation)** of the vehicle, completely independent of how the phone is physically mounted.

### Step 2.4: Feature Engineering (`engineer.py`)
The pipeline extracts exactly **3 physical features** for the model:
1.  **`ACC_MAG` (Acceleration Magnitude):** The total Euclidean norm of the accelerometer vector ($\sqrt{x^2 + y^2 + z^2}$).
2.  **`PROJ_YAW` (Projected Yaw):** The gyroscope rotation around the gravity vector, representing the vehicle's turning rate.
3.  **`DYN_ACC_MAG` (Dynamic Acceleration Magnitude):** The magnitude of acceleration after subtracting the gravity vector, representing the pure forward/backward/lateral physical forces acting on the vehicle.

- **Windowing:** The model does not look at single frames. It uses a **sliding window of 10 timesteps** (1.0 second of context) to predict the vehicle's motion at the end of the window.

---

## 3. Model Architecture

The `DeepIDRModel` is built using a **1-Dimensional Convolutional Neural Network (1D-CNN)** architecture. CNNs are exceptional at extracting temporal patterns and micro-vibrational signatures from time-series sensor data.

### Architecture Details
- **Input Shape:** `(Batch_Size, 10, 3)` -> 10 timesteps, 3 features.
- **Layer 1 (Conv1D):** 32 filters, Kernel Size 3, ReLU Activation.
- **Layer 2 (Conv1D):** 64 filters, Kernel Size 3, ReLU Activation, followed by Dropout (0.2).
- **Flattening:** The temporal sequence is flattened into a single feature vector.
- **Fully Connected (Dense) Layers:**
  - Dense(128) + ReLU + Dropout(0.2)
  - Dense(64) + ReLU
- **Output Layer:** Dense(2) -> Outputting `Velocity` (km/h) and `Yaw Rate` (degrees/sec).

By keeping the architecture lightweight, the model is highly optimized for real-time edge deployment (e.g., via ONNX Runtime on iOS/Android devices).

---

## 4. Training Methodology

To prevent overfitting and ensure the model learns universal physics rather than memorizing a specific route, the following rigorous training protocol is used:

### Combined Dataset Generalization
The model is trained simultaneously on over **450,000 samples** spanning multiple independent drivers, vehicles, and geographic locations.
- **Train Set:** `S1`, `S2`, `S4`
- **Validation Set:** `S3b`, `S3c`, `M` (Unseen vehicle/driver used for Early Stopping)
- **Test Set:** `Y1` (Zero-shot test on an entirely unseen driver and vehicle)

### Normalization Strategy
- A global `StandardScaler` (Mean and Standard Deviation) is fitted **strictly on the Train Set**.
- These exact parameters are saved to `norm_params_combined.json` and applied identically during Validation, Testing, and ultimately Deployment. This prevents data leakage.

### Optimization
- **Loss Function:** Mean Squared Error (MSE).
- **Optimizer:** Adam Optimizer with an initial learning rate of `0.001`.
- **Learning Rate Scheduler:** `StepLR` reduces the learning rate by 50% every 10 epochs to ensure smooth convergence.
- **Early Stopping:** Training monitors the Validation Loss and halts if performance stops improving, preventing overfitting.

---

## 5. Deployment (ONNX)

Upon successful training and evaluation, the best model weights are exported to the Open Neural Network Exchange (ONNX) format (`deep_idr.onnx`). 

The ONNX model supports **dynamic batch sizes**, allowing it to process real-time sensor streams frame-by-frame on mobile devices with sub-millisecond latency.
