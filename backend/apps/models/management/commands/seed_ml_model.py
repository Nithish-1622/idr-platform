import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.models.models import MLModel, ModelArtifact, ModelVersion
from apps.models.services import publish_model_version_service
from common.contract_validator import transform_to_canonical_contract, validate_model_contract
from common.storage import StorageService

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
CONTRACT_DIR = BASE_DIR / "contracts" / "model"
ML_DIR = BASE_DIR / "ml" / "models" / "deploy"


class Command(BaseCommand):
    help = "Seeds the backend database with ML dev1's deep_idr_model ONNX artifact and contract specs."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding ML dev1 Deep IDR Model and Contract..."))

        contract_file = CONTRACT_DIR / "deep-idr-model.json"
        preprocessing_file = CONTRACT_DIR / "preprocessing.json"
        onnx_file = ML_DIR / "deep_idr.onnx"

        if not contract_file.exists():
            self.stderr.write(self.style.ERROR(f"Contract file missing: {contract_file}"))
            return
        if not preprocessing_file.exists():
            self.stderr.write(self.style.ERROR(f"Preprocessing file missing: {preprocessing_file}"))
            return
        if not onnx_file.exists():
            self.stderr.write(self.style.ERROR(f"ONNX model file missing: {onnx_file}"))
            return

        with open(contract_file, "r", encoding="utf-8") as f:
            raw_contract = json.load(f)

        with open(preprocessing_file, "r", encoding="utf-8") as f:
            preprocessing_data = json.load(f)

        with open(onnx_file, "rb") as f:
            onnx_bytes = f.read()

        # Validate canonical schema
        canonical_contract = transform_to_canonical_contract(raw_contract)
        validate_model_contract(canonical_contract)
        self.stdout.write(self.style.SUCCESS("[OK] ML Model Contract successfully validated against schema.json!"))

        model_name = raw_contract.get("model", {}).get("name", "deep_idr_model")
        version_str = raw_contract.get("model", {}).get("version", "1.0.0")

        with transaction.atomic():
            ml_model, _ = MLModel.objects.get_or_create(
                name=model_name,
                defaults={
                    "model_type": MLModel.ModelType.IDR_RECURRENT,
                    "description": raw_contract.get("model", {}).get("purpose", "IDR 1D-CNN Navigation Model"),
                },
            )

            # Save ONNX binary artifact using StorageService
            storage_path, checksum, file_size = StorageService.save_artifact(
                f"models/onnx/{model_name}_{version_str}.onnx", onnx_bytes
            )

            model_version, created = ModelVersion.objects.get_or_create(
                ml_model=ml_model,
                semantic_version=version_str,
                defaults={
                    "status": ModelVersion.Status.APPROVED,
                    "min_app_version": "1.0.0",
                    "supported_platforms": ["ANDROID", "IOS"],
                    "opset_version": raw_contract.get("model", {}).get("opset", 14),
                    "input_schema": raw_contract.get("input", {}),
                    "output_schema": raw_contract.get("output", {}),
                    "preprocessing_spec": preprocessing_data.get("preprocessing", {}),
                    "contract_spec": canonical_contract,
                },
            )

            if not created:
                model_version.status = ModelVersion.Status.APPROVED
                model_version.opset_version = raw_contract.get("model", {}).get("opset", 14)
                model_version.input_schema = raw_contract.get("input", {})
                model_version.output_schema = raw_contract.get("output", {})
                model_version.preprocessing_spec = preprocessing_data.get("preprocessing", {})
                model_version.contract_spec = canonical_contract
                model_version.save()

            # Attach / update ModelArtifact
            artifact, _ = ModelArtifact.objects.get_or_create(
                model_version=model_version,
                defaults={
                    "format": raw_contract.get("model", {}).get("format", "ONNX"),
                    "file_path": storage_path,
                    "checksum_sha256": checksum,
                    "file_size_bytes": file_size,
                },
            )
            artifact.file_path = storage_path
            artifact.checksum_sha256 = checksum
            artifact.file_size_bytes = file_size
            artifact.save()

            # Publish version as ACTIVE deployment
            publish_model_version_service(model_version, target_platform="ALL")

        self.stdout.write(
            self.style.SUCCESS(
                f"[SUCCESS] Registered and published '{model_name}' v{version_str} ONNX model!"
            )
        )
