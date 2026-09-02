# Mobile Backend ONNX Model Integration & Network Protocol Guide
**SIH-2026 Intelligent Dead Reckoning (IDR) Navigation System**

This guide specifies how the **Mobile Backend** / **Mobile Core Engine** fetches, verifies, and integrates the production ONNX model (`deep_idr.onnx`) from the main Django IDR backend over Local Wi-Fi / IPv4 network protocols.

---

## 1. Network Architecture Overview

```
┌──────────────────────────────────────┐               ┌──────────────────────────────────────┐
│        Main Django Backend           │               │     Mobile Backend / Mobile App      │
│   (http://<SERVER_IPV4>:8000/api/v1) │               │       (Client / Sensor Loop)         │
├──────────────────────────────────────┤               ├──────────────────────────────────────┤
│  • Latest Active Model Metadata      │ ◄─ HTTP GET ─ │ 1. Fetch Contract & Metadata         │
│  • Binary Stream: model.onnx         │ ◄─ HTTP GET ─ │ 2. Download ONNX Binary Stream       │
│  • Checksum & Verification Headers   │               │ 3. Verify SHA256 & Load ONNX Runtime │
└──────────────────────────────────────┘               └──────────────────────────────────────┘
```

---

## 2. API Endpoints for ONNX Model Delivery

### Endpoint 1: Model Contract & Metadata Protocol
- **HTTP Method**: `GET`
- **Path**: `/api/v1/models/latest/contract/`
- **URL**: `http://<SERVER_IPV4>:8000/api/v1/models/latest/contract/`
- **Description**: Returns model version metadata, input/output schemas, opset version, SHA256 checksum, and the direct binary `download_url`.

#### Sample Response (`200 OK`):
```json
{
  "model": {
    "name": "deep_idr_model",
    "version": "1.0.0",
    "format": "ONNX",
    "opset": 14,
    "artifact_url": "http://10.57.1.175:8000/api/v1/models/latest/download/",
    "download_url": "http://10.57.1.175:8000/api/v1/models/latest/download/",
    "checksum_sha256": "d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980",
    "file_size_bytes": 3072
  },
  "input": {
    "tensor_name": "imu_window",
    "shape": [1, 100, 6],
    "dtype": "float32",
    "channels": ["ax", "ay", "az", "gx", "gy", "gz"],
    "sampling_frequency_hz": 100
  },
  "output": {
    "tensor_name": "delta_pose",
    "shape": [1, 3],
    "dtype": "float32",
    "elements": ["dx_m", "dy_m", "dheading_rad"]
  },
  "preprocessing": {
    "accel_scale": 1.0,
    "gyro_scale": 1.0,
    "window_size": 100,
    "stride": 10
  }
}
```

---

### Endpoint 2: Binary ONNX Stream Delivery
- **HTTP Method**: `GET`
- **Paths**:
  - Direct Endpoint: `http://<SERVER_IPV4>:8000/api/v1/models/latest/download/`
  - Direct Binary Shortcut: `http://<SERVER_IPV4>:8000/api/v1/model.onnx`
- **Description**: Streams the raw binary `.onnx` model file with integrity verification headers.

#### HTTP Response Headers (`200 OK`):
```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="deep_idr_model_v1.0.0.onnx"
Content-Length: 3072
X-Model-Name: deep_idr_model
X-Model-Version: 1.0.0
X-Model-Opset: 14
X-Model-Checksum-SHA256: d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980
ETag: "d5a4720a3f24352e4bc5cb811cafc88880579f43e7f58b5f658d14530a4a0980"
```

---

## 3. Implementation Blueprint for Mobile Backend / Mobile Developer

### Step 1: Download and Save `.onnx` File (Python Example)

```python
import hashlib
import requests

SERVER_IP = "10.57.1.175"  # Replace with Django Server IPv4
CONTRACT_URL = f"http://{SERVER_IP}:8000/api/v1/models/latest/contract/"
MODEL_OUTPUT_PATH = "deep_idr.onnx"

def fetch_and_verify_onnx_model():
    # 1. Fetch Contract & Expected Checksum
    contract_res = requests.get(CONTRACT_URL).json()
    model_meta = contract_res["model"]
    download_url = model_meta["download_url"]
    expected_checksum = model_meta["checksum_sha256"]
    
    print(f"Downloading model '{model_meta['name']}' v{model_meta['version']}...")

    # 2. Download ONNX Binary Stream
    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    sha256 = hashlib.sha256()
    with open(MODEL_OUTPUT_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                sha256.update(chunk)

    downloaded_checksum = sha256.hexdigest()

    # 3. Verify SHA256 Checksum
    if downloaded_checksum.lower() == expected_checksum.lower():
        print("✅ ONNX Model Downloaded and SHA256 Checksum Verified!")
        return MODEL_OUTPUT_PATH
    else:
        raise ValueError(
            f"Checksum Mismatch! Expected {expected_checksum}, got {downloaded_checksum}"
        )

if __name__ == "__main__":
    fetch_and_verify_onnx_model()
```

---

### Step 2: Load ONNX Model & Run Inference (`onnxruntime`)

```python
import numpy as np
import onnxruntime as ort

# Load downloaded ONNX model session
session = ort.InferenceSession("deep_idr.onnx")

# Prepare dummy IMU window input: shape (1, 100, 6) -> [batch, 100 samples, 6 IMU channels]
# Channels: [accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z]
imu_window_data = np.random.randn(1, 100, 6).astype(np.float32)

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

# Run ONNX inference
outputs = session.run([output_name], {input_name: imu_window_data})
delta_pose = outputs[0]  # Returns [dx_m, dy_m, dheading_rad]

print("Inference Output [dx_m, dy_m, dheading_rad]:", delta_pose)
```

---

## 4. Summary of URLs to Access over Local Wi-Fi

| Resource | Wi-Fi Endpoint URL | Description |
| :--- | :--- | :--- |
| **Model Contract Metadata** | `http://<SERVER_IPV4>:8000/api/v1/models/latest/contract/` | Input/Output shape & metadata JSON |
| **ONNX Binary Download** | `http://<SERVER_IPV4>:8000/api/v1/models/latest/download/` | Direct binary stream of `.onnx` file |
| **Direct Model Shortcut** | `http://<SERVER_IPV4>:8000/api/v1/model.onnx` | Direct binary shortcut |
| **IMU Ingestion Gateway** | `http://<SERVER_IPV4>:8000/api/v1/get_imu` | Telemetry & navigation state API |
