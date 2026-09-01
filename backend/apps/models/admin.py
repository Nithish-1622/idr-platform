from django.contrib import admin

from .models import Deployment, MLModel, ModelVersion


class ModelVersionInline(admin.TabularInline):
    model = ModelVersion
    extra = 0


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ("name", "model_type", "created_at")
    inlines = [ModelVersionInline]


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = (
        "ml_model",
        "semantic_version",
        "status",
        "min_app_version",
        "release_date",
    )
    list_filter = ("status", "ml_model")
    search_fields = ("semantic_version", "ml_model__name")


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ("model_version", "target_platform", "is_active", "deployed_at")
    list_filter = ("target_platform", "is_active")
