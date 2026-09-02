import torch
import os
import sys

sys.path.append(r"e:\idr-platform")
from ml.src.training.models import DeepIDRModel

def export_onnx():
    device = torch.device('cpu')
    model = DeepIDRModel(window_size=10, num_features=3).to(device)
    
    # Load the best combined weights
    model_path = r"e:\idr-platform\ml\models\checkpoints\best_combined_model.pth"
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    # Create dummy input based on our architecture: (batch_size, window_size, num_features)
    # Batch size can be dynamic, but for export we provide a sample tensor
    dummy_input = torch.randn(1, 10, 3).to(device)
    
    export_path = r"e:\idr-platform\ml\models\deploy\deep_idr.onnx"
    
    print(f"Exporting model from {model_path} to {export_path}...")
    
    torch.onnx.export(
        model, 
        dummy_input, 
        export_path, 
        export_params=True, 
        opset_version=14,          # Opset 14 is highly compatible with modern ONNX Runtime
        do_constant_folding=True,  # Optimizes the graph
        input_names=['input'],     
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},    # Allow variable batch size
            'output': {0: 'batch_size'}
        }
    )
    
    print(f"ONNX Export Complete! Saved to: {export_path}")

if __name__ == '__main__':
    export_onnx()
