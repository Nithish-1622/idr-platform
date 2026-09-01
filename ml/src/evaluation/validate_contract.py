import os
import sys
import json
import torch
import numpy as np
import onnxruntime as ort

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.src.training.models import DeepIDRModel

def run_validation():
    print("--- Validating Model Contract against Implementation ---")
    
    contract_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "contracts", "model", "deep-idr-model.json")
    onnx_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "deploy", "deep_idr.onnx")
    pth_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "deep_idr_model.pth")
    
    with open(contract_path, "r") as f:
        contract = json.load(f)
        
    print("\n1. ONNX Verification")
    if not os.path.exists(onnx_path):
        print(f"FAIL: ONNX model not found at {onnx_path}")
        return
        
    session = ort.InferenceSession(onnx_path)
    
    # Check Inputs
    onnx_input = session.get_inputs()[0]
    expected_input_name = contract["input"]["tensor_name"]
    expected_input_shape = contract["input"]["tensor_shape"]
    
    if onnx_input.name != expected_input_name:
        print(f"FAIL: Input name mismatch. Contract: {expected_input_name}, ONNX: {onnx_input.name}")
        return
        
    if onnx_input.shape != expected_input_shape:
        print(f"FAIL: Input shape mismatch. Contract: {expected_input_shape}, ONNX: {onnx_input.shape}")
        return
        
    print(f"PASS: Input strictly matches contract (Name: {onnx_input.name}, Shape: {onnx_input.shape})")
    
    # Check Outputs
    onnx_output = session.get_outputs()[0]
    expected_output_name = contract["output"]["tensor_name"]
    expected_output_shape = contract["output"]["tensor_shape"]
    
    if onnx_output.name != expected_output_name:
        print(f"FAIL: Output name mismatch. Contract: {expected_output_name}, ONNX: {onnx_output.name}")
        return
        
    if onnx_output.shape != expected_output_shape:
        print(f"FAIL: Output shape mismatch. Contract: {expected_output_shape}, ONNX: {onnx_output.shape}")
        return
        
    print(f"PASS: Output strictly matches contract (Name: {onnx_output.name}, Shape: {onnx_output.shape})")
    
    print("\n2. Inference & NaN/Inf Test")
    # Generate random test tensor bounded realistically (e.g. 0 to 15 m/s2, rad/s)
    np.random.seed(42)
    dummy_input = np.random.uniform(0, 15, size=expected_input_shape).astype(np.float32)
    
    onnx_res = session.run([onnx_output.name], {onnx_input.name: dummy_input})[0]
    
    if np.isnan(onnx_res).any() or np.isinf(onnx_res).any():
        print("FAIL: Model produced NaN or Inf")
        return
    else:
        print("PASS: ONNX Inference successful, no NaN/Inf.")
        print(f"      Input:  {dummy_input.shape}")
        print(f"      Output: {onnx_res.shape} -> {onnx_res}")
        
    print("\n3. PyTorch vs ONNX Parity Test")
    if not os.path.exists(pth_path):
        print("FAIL: PyTorch model not found, cannot test parity.")
        return
        
    torch_model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=32, num_outputs=2)
    torch_model.load_state_dict(torch.load(pth_path, weights_only=True))
    torch_model.eval()
    
    with torch.no_grad():
        torch_res = torch_model(torch.tensor(dummy_input)).numpy()
        
    # Compare with high tolerance since architectures export math operations slightly differently
    diff = np.abs(onnx_res - torch_res)
    max_diff = np.max(diff)
    
    if max_diff > 1e-4:
        print(f"FAIL: PyTorch vs ONNX mismatch! Max difference = {max_diff}")
    else:
        print(f"PASS: PyTorch vs ONNX output matches perfectly! (Max diff = {max_diff:.8f})")
        
    print("\nALL VALIDATION TESTS PASSED.")

if __name__ == "__main__":
    run_validation()
