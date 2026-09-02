import numpy as np


class DisturbanceEngine:
    """
    Composable disturbance pipeline to apply realistic noise, bias, drift,
    scale factor errors, and sensor dropouts without mutating ground truth state.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def add_gaussian_noise(self, values: np.ndarray, std: float) -> np.ndarray:
        """Adds zero-mean Gaussian noise with specified standard deviation."""
        if std <= 0.0:
            return values
        noise = self.rng.normal(0.0, std, size=values.shape)
        return values + noise

    def add_constant_bias(self, values: np.ndarray, bias: np.ndarray) -> np.ndarray:
        """Adds constant bias offset vector."""
        return values + np.asarray(bias)

    def add_random_walk_drift(self, values: np.ndarray, drift_rate: float, dt: float, step_idx: int) -> np.ndarray:
        """Applies random walk drift accumulating over simulation steps."""
        if drift_rate <= 0.0:
            return values
        drift_std = drift_rate * np.sqrt(dt * step_idx)
        drift = self.rng.normal(0.0, drift_std, size=values.shape)
        return values + drift

    def apply_scale_factor(self, values: np.ndarray, scale_error_pct: float) -> np.ndarray:
        """Applies scale factor error percentage (e.g. 0.01 for 1% scale error)."""
        scale_factor = 1.0 + (scale_error_pct / 100.0 if scale_error_pct > 1.0 else scale_error_pct)
        return values * scale_factor

    def apply_dropout(self, values: np.ndarray, dropout_prob: float) -> np.ndarray:
        """Applies random sensor dropouts (setting to 0 or NaN)."""
        if dropout_prob <= 0.0:
            return values
        if self.rng.uniform(0.0, 1.0) < dropout_prob:
            return np.zeros_like(values)
        return values
