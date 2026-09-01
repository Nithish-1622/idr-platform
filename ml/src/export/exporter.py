import torch
import torch.onnx
import os

class ONNXExporter:
    def __init__(self, model: torch.nn.Module, window_size: int = 10, num_features: int = 3):
        self.model = model
        self.window_size = window_size
        self.num_features = num_features
        
    def export(self, weights_path: str, output_path: str):
        """
        Exports the PyTorch model to ONNX with static batch size 1.
        """
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Weights not found at {weights_path}")
            
        self.model.load_state_dict(torch.load(weights_path, weights_only=True))
        self.model.eval()
        
        # Static batch size of 1 for mobile execution
        dummy_input = torch.randn(1, self.window_size, self.num_features)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"Exporting model to {output_path}...")
        torch.onnx.export(
            self.model, 
            dummy_input, 
            output_path,
            export_params=True,
            opset_version=14,          # Opset 14 is widely supported by ORT Mobile
            do_constant_folding=True,
            input_names=['imu_window'],
            output_names=['kinematics']
            # We don't use dynamic_axes since static batch size was chosen
        )
        print("Export successful!")
