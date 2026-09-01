import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.src.training.models import DeepIDRModel
from ml.src.export.exporter import ONNXExporter

def run_export_pipeline():
    print("--- Running ONNX Export Pipeline ---")
    
    weights_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "deep_idr_model.pth")
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "deploy", "deep_idr.onnx")
    
    if not os.path.exists(weights_path):
        print(f"Error: No trained model found at {weights_path}")
        print("Please run the training pipeline first.")
        return
        
    model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=32, num_outputs=2)
    exporter = ONNXExporter(model=model, window_size=10, num_features=3)
    
    exporter.export(weights_path, output_path)

if __name__ == "__main__":
    run_export_pipeline()
