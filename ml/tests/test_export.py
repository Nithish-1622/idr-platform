import os
import torch
import onnx
from src.training.models import DeepIDRModel
from src.export.exporter import ONNXExporter

def test_onnx_export(tmp_path):
    # Setup dummy model
    model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=8, num_outputs=2)
    weights_path = os.path.join(tmp_path, "dummy_model.pth")
    torch.save(model.state_dict(), weights_path)
    
    output_path = os.path.join(tmp_path, "deep_idr.onnx")
    
    exporter = ONNXExporter(model=model, window_size=10, num_features=3)
    exporter.export(weights_path, output_path)
    
    assert os.path.exists(output_path)
    
    # Validate the ONNX graph
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
