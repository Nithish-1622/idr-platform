from django.urls import path
from .views import (
    MobileGetIMUView,
    SimulationDetailView,
    SimulationListView,
    SimulationPresetListView,
    SimulationPreviewView,
    SimulationRunTriggerView,
)

app_name = "simulations"

urlpatterns = [
    path("simulations/", SimulationListView.as_view(), name="list"),
    path("simulations/presets/", SimulationPresetListView.as_view(), name="presets"),
    path("simulations/preview", SimulationPreviewView.as_view(), name="preview"),
    path("simulations/<uuid:pk>/", SimulationDetailView.as_view(), name="detail"),
    path("simulations/<uuid:pk>/run/", SimulationRunTriggerView.as_view(), name="trigger"),
    path("get_imu", MobileGetIMUView.as_view(), name="get_imu"),
]
