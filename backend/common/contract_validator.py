import json
import logging
from pathlib import Path
from typing import Any

import jsonschema

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = BASE_DIR / "contracts" / "model" / "schema.json"


def load_contract_schema() -> dict[str, Any]:
    """Loads the canonical IDRModelContract JSON schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Contract schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_to_canonical_contract(raw_contract: dict[str, Any], sampling_hz: float = 10.0) -> dict[str, Any]:
    """
    Transforms dev1's deep-idr-model.json layout into the schema.json compliant layout if needed.
    """
    if "model_name" in raw_contract:
        return raw_contract

    model_info = raw_contract.get("model", {})
    input_info = raw_contract.get("input", {})
    output_info = raw_contract.get("output", {})

    features = [f.get("name", "") for f in input_info.get("features", [])]
    predictions = [f.get("name", "") for f in output_info.get("features", [])]

    return {
        "model_name": model_info.get("name", "deep_idr_model"),
        "version": model_info.get("version", "1.0.0"),
        "model_format": model_info.get("format", "ONNX"),
        "input_schema": {
            "tensor_shape": input_info.get("tensor_shape", [1, 10, 3]),
            "features": features if features else ["ACC_MAG", "GYRO_MAG", "DYN_ACC_MAG"],
            "sampling_frequency_hz": sampling_hz,
        },
        "output_schema": {
            "tensor_shape": output_info.get("tensor_shape", [1, 2]),
            "predictions": predictions if predictions else ["Velocity", "Yaw Rate"],
        },
        "compatibility": {
            "min_app_version": "1.0.0",
            "supported_platforms": ["ANDROID", "IOS"],
        },
    }


def validate_model_contract(contract_data: dict[str, Any]) -> bool:
    """
    Validates a model contract dictionary against contracts/model/schema.json.
    """
    schema = load_contract_schema()
    jsonschema.validate(instance=contract_data, schema=schema)
    return True
