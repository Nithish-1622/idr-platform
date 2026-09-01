import torch
from src.training.models import DeepIDRModel

def test_deep_model_forward():
    model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=16, num_outputs=2)
    
    # Create dummy input (Batch, Window, Features)
    dummy_x = torch.randn(32, 10, 3)
    
    out = model(dummy_x)
    
    assert out.shape == (32, 2) # Should output (Batch, 2) for Velocity and Yaw Rate
