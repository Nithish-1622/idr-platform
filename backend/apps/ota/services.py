from typing import Any

from apps.models.models import Deployment

from .models import UpdateManifest


def check_for_updates_service(
    platform: str,
    app_version: str,
    current_model_version: str = "",
    current_map_version: str = "",
) -> list[dict[str, Any]]:
    """Evaluates available compatible updates for mobile device."""
    available_updates = []

    # Check Model Updates
    active_deployment = (
        Deployment.objects.filter(is_active=True, target_platform__in=[platform, "ALL"])
        .select_related("model_version", "model_version__artifact")
        .first()
    )

    if active_deployment:
        mv = active_deployment.model_version
        if mv.semantic_version != current_model_version:
            artifact = getattr(mv, "artifact", None)
            if artifact:
                available_updates.append(
                    {
                        "payload_type": "MODEL",
                        "target_version": mv.semantic_version,
                        "artifact_url": (
                            artifact.file_path.url if artifact.file_path else ""
                        ),
                        "checksum_sha256": artifact.checksum_sha256,
                        "file_size_bytes": artifact.file_size_bytes,
                        "min_app_version": mv.min_app_version,
                        "is_mandatory": False,
                        "release_notes": f"Active IDR model update v{mv.semantic_version}",
                    }
                )

    # Check Explicit OTA Manifests
    manifests = UpdateManifest.objects.filter(
        target_platform__in=[platform, "ALL"]
    ).order_by("-created_at")

    for m in manifests:
        if m.payload_type == "MODEL" and m.target_version == current_model_version:
            continue
        if m.payload_type == "MAP" and m.target_version == current_map_version:
            continue

        available_updates.append(
            {
                "id": str(m.id),
                "payload_type": m.payload_type,
                "target_version": m.target_version,
                "artifact_url": m.artifact_url,
                "checksum_sha256": m.checksum_sha256,
                "file_size_bytes": m.file_size_bytes,
                "min_app_version": m.min_app_version,
                "is_mandatory": m.is_mandatory,
                "release_notes": m.release_notes,
            }
        )

    return available_updates
