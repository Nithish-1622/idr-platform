# SIH 2026: Intelligent Dead Reckoning (IDR) Platform

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Platform](https://img.shields.io/badge/Platform-Edge%20AI%20%7C%20Backend-blue)

Welcome to the **Intelligent Dead Reckoning (IDR) Platform**, the complete backend, simulation, and machine learning ecosystem for our Smart India Hackathon (SIH) 2026 project.

## 🎯 Purpose
Modern navigation systems completely fail when a vehicle enters a tunnel, a deep urban canyon, or loses internet/GPS connections. **Deep IDR** solves this by turning a standard smartphone into a highly accurate Inertial Navigation System. 

When satellite signals drop, our offline **1D-CNN Artificial Intelligence** model seamlessly takes over. By processing raw forces from the phone's built-in IMU (Accelerometer and Gyroscope), the AI perfectly estimates the vehicle's velocity and yaw rate to provide uninterrupted, highly accurate routing.

## ✨ Key Features
- **Zero-Signal Navigation:** Continues navigating offline using pure AI dead-reckoning.
- **Rotation-Invariant AI:** Uses gravity-isolation and vector projection so the app works perfectly regardless of how the phone is mounted in the car (upside down, tilted, etc.).
- **Ultra-Low Latency:** Edge-optimized ONNX model running at just `0.5 ms` per inference frame.
- **Advanced Simulation Engine:** A robust Python-based engine capable of synthesizing real-world environments, injecting multipath noise, and simulating exact GNSS blackouts.
- **Automated Validation Pipeline:** 25 rigorous test cases proving a remarkable **1.71% drift rate** on unseen real-world data.

---

## 📂 Repository Structure

The project is cleanly divided into specific microservices and domains:

```text
idr-platform/
│
├── backend/            # Django REST API (Control Plane)
│                       # Manages device registration, dataset metadata, and simulation histories.
│
├── ml/                 # Machine Learning Pipeline
│   ├── src/            # PyTorch Model, filtering, training, and feature engineering.
│   ├── models/         # Trained .onnx edge deployment files.
│   └── scratch/        # Analytics, shift alignment scripts, and sanity checks.
│
├── simulation/         # The Simulation Engine
│   ├── scenario/       # Real-world presets (e.g., Sri Eshwar College Demo).
│   ├── disturbances/   # GNSS outage generators and noise injection.
│   └── trajectory/     # Geographic math and coordinate conversions.
│
├── contracts/          # System Schemas
│   ├── api/            # OpenAPI / Swagger specifications.
│   └── model/          # Input/Output schema definitions for the ONNX edge model.
│
└── docs/               # Technical Documentation
    ├── architecture/   # System design and integration diagrams.
    └── ml/             # Extensive model performance and I/O reports.
```

---

## 🚀 Getting Started

### 1. The Sri Eshwar College Demonstration
We have built a custom, real-world demonstration route specifically for our SIH pitch. 
- **Scenario ID:** `sri_eshwar_outage`
- **What it does:** Starts a vehicle driving from the Sri Eshwar College campus. At exactly 2 minutes and 24 seconds, it simulates a massive, 56-second total loss of GPS and Internet. The Deep IDR ML model proves its capability by seamlessly taking over dead-reckoning without halting or losing track of the real road.

### 2. Exploring the ML Pipeline
To understand how raw noisy sensor data is transformed into stable predictions:
- Check out `ml/src/features/engineer.py` for the rotation-invariance logic.
- View `docs/ml/deep_idr_model_performance.md` for our validation metrics.

### 3. API & Backend
The backend serves as the control plane for triggering simulations and managing edge devices. Refer to `docs/simulation_endpoints.md` for the exact JSON payloads used to interact with the engine.

---

## 🛠️ Built With
- **Machine Learning:** PyTorch, ONNX, Pandas, NumPy, SciPy
- **Backend APIs:** Python, Django, REST Framework
- **Simulation Math:** Haversine, Equirectangular Projection algorithms
