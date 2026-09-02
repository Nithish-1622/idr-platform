from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.views import HealthLiveView, HealthReadyView
from apps.simulations.views import (
    EventRoadDisturbanceView,
    EventTurnView,
    EventVibrationView,
    FusionUpdateView,
    MobileGetIMUView,
    ONNXInferenceView,
    RoadContextView,
    ShadowDRErrorView,
    TrajectoryObservationView,
)
from apps.models.views import LatestModelDownloadView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health Checks (Supports /health/live, /health/live/, /api/v1/health/live, /api/v1/health/live/)
    path("health", HealthLiveView.as_view(), name="health_root"),
    path("health/", HealthLiveView.as_view(), name="health_root_slash"),
    path("health/live", HealthLiveView.as_view(), name="health_live"),
    path("health/live/", HealthLiveView.as_view(), name="health_live_slash"),
    path("health/ready", HealthReadyView.as_view(), name="health_ready"),
    path("health/ready/", HealthReadyView.as_view(), name="health_ready_slash"),
    path("api/v1/health/live", HealthLiveView.as_view(), name="api_health_live"),
    path("api/v1/health/live/", HealthLiveView.as_view(), name="api_health_live_slash"),
    path("api/v1/health/ready", HealthReadyView.as_view(), name="api_health_ready"),
    path("api/v1/health/ready/", HealthReadyView.as_view(), name="api_health_ready_slash"),

    # Root Level Master Addon Aliases
    path("onnx/inference", ONNXInferenceView.as_view(), name="root_onnx_inference"),
    path("fusion/update", FusionUpdateView.as_view(), name="root_fusion_update"),
    path("events/vibration", EventVibrationView.as_view(), name="root_event_vibration"),
    path("events/turn", EventTurnView.as_view(), name="root_event_turn"),
    path("events/road-disturbance", EventRoadDisturbanceView.as_view(), name="root_event_road_disturbance"),
    path("trajectory/observation", TrajectoryObservationView.as_view(), name="root_trajectory_observation"),
    path("dr/error", ShadowDRErrorView.as_view(), name="root_dr_error"),
    path("road/context", RoadContextView.as_view(), name="root_road_context"),

    # OpenAPI Schema & Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Direct Mobile Ingestion & Binary Download Routes
    path("api/v1/get_imu", MobileGetIMUView.as_view(), name="mobile_get_imu"),
    path("api/v1/model.onnx", LatestModelDownloadView.as_view(), name="direct_model_onnx"),
    path("api/v1/models/download", LatestModelDownloadView.as_view(), name="direct_model_download"),

    # Versioned API V1 Endpoints
    path("api/v1/", include("apps.accounts.urls", namespace="accounts")),
    path("api/v1/", include("apps.devices.urls", namespace="devices")),
    path("api/v1/", include("apps.datasets.urls", namespace="datasets")),
    path("api/v1/", include("apps.models.urls", namespace="models")),
    path("api/v1/", include("apps.maps.urls", namespace="maps")),
    path("api/v1/", include("apps.telemetry.urls", namespace="telemetry")),
    path("api/v1/", include("apps.configurations.urls", namespace="configurations")),
    path("api/v1/", include("apps.ota.urls", namespace="ota")),
    path("api/v1/", include("apps.analytics.urls", namespace="analytics")),
    path("api/v1/", include("apps.simulations.urls", namespace="simulations")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
