# Dev1 ML Model Contract

This directory contains the formal contract for the **Deep IDR (Intelligent Dead Reckoning)** machine learning model created by Dev1. 

**Consumer:** Dev3 (Integration / Mobile Team)

## What this model does
The model predicts the continuous forward `Velocity` (m/s) and `Yaw Rate` (rad/s) of a vehicle strictly using a smartphone's IMU sensors, regardless of the smartphone's orientation inside the vehicle.

## Currently Active Model
- **Name:** `deep_idr_model`
- **Version:** `1.0.0`
- **Artifact:** `ml/models/deploy/deep_idr.onnx`
- **Type:** 1D-CNN (Convolutional Neural Network)
- **Statefulness:** Completely stateless. All temporal context is derived entirely from the 10-timestep sliding window passed in as input.

## How to Integrate
1. Read `deep-idr-model.json` to understand the exact tensor shapes, names, and data types expected by the ONNX graph.
2. Read `preprocessing.json` to understand exactly how raw Android sensors must be mathematically converted into the `[1, 10, 3]` input tensor.
3. Feed the resulting tensor to the ONNX runtime.
4. Extract `Velocity` and `Yaw Rate` from the output tensor and feed them into the physics-based Dead Reckoning navigation state.

## Compatibility Checks
If Dev1 releases a new model version, they will update `deep-idr-model.json`. Before deploying the new ONNX file, Dev3 should diff `deep-idr-model.json` against the previous version to detect any changes in input shapes, feature counts, or units.
