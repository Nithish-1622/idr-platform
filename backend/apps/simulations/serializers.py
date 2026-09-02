from rest_framework import serializers
from .models import SimulationRun


class SimulationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationRun
        fields = [
            "id",
            "scenario_id",
            "scenario_name",
            "seed",
            "duration_seconds",
            "status",
            "scenario_config",
            "metrics",
            "gnss_outage_evaluations",
            "artifact_paths",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
        ]
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        paths = instance.artifact_paths or {}
        abs_paths = {}

        for k, v in paths.items():
            if isinstance(v, str) and v.startswith("/media/"):
                if request:
                    abs_paths[k] = request.build_absolute_uri(v)
                else:
                    abs_paths[k] = f"http://127.0.0.1:8000{v}"
            else:
                abs_paths[k] = v

        data["artifact_paths"] = abs_paths
        return data


class SimulationRunCreateSerializer(serializers.Serializer):
    preset_id = serializers.CharField(required=False, allow_blank=True, default="flagship_gnss_outage")
    scenario_id = serializers.CharField(required=False, allow_blank=True)
    seed = serializers.IntegerField(required=False, default=42)
    duration_seconds = serializers.FloatField(required=False, default=300.0)
    custom_scenario = serializers.DictField(required=False)
