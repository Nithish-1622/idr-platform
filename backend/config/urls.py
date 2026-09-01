from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.views import HealthLiveView, HealthReadyView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health Checks
    path("health/live", HealthLiveView.as_view(), name="health_live"),
    path("health/ready", HealthReadyView.as_view(), name="health_ready"),
    # OpenAPI Schema & Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
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
]
