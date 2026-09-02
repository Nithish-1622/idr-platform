from django.urls import path
from .views import (
    EventRoadDisturbanceView,
    EventTurnView,
    EventVibrationView,
    FusionUpdateView,
    MobileGetIMUView,
    ONNXInferenceView,
    RoadContextView,
    ShadowDRErrorView,
    SimulationDetailView,
    SimulationListView,
    SimulationPresetListView,
    SimulationPreviewView,
    SimulationRunTriggerView,
    TrajectoryObservationView,
)

app_name = "simulations"

urlpatterns = [
    path("simulations/", SimulationListView.as_view(), name="list"),
    path("simulations/presets/", SimulationPresetListView.as_view(), name="presets"),
    path("simulations/preview", SimulationPreviewView.as_view(), name="preview"),
    path("simulations/<uuid:pk>/", SimulationDetailView.as_view(), name="detail"),
    path("simulations/<uuid:pk>/run/", SimulationRunTriggerView.as_view(), name="trigger"),
    path("get_imu", MobileGetIMUView.as_view(), name="get_imu"),
    # Master Spec Addons
    path("onnx/inference", ONNXInferenceView.as_view(), name="onnx_inference"),
    path("fusion/update", FusionUpdateView.as_view(), name="fusion_update"),
    path("events/vibration", EventVibrationView.as_view(), name="event_vibration"),
    path("events/turn", EventTurnView.as_view(), name="event_turn"),
    path("events/road-disturbance", EventRoadDisturbanceView.as_view(), name="event_road_disturbance"),
    path("trajectory/observation", TrajectoryObservationView.as_view(), name="trajectory_observation"),
    path("dr/error", ShadowDRErrorView.as_view(), name="dr_error"),
    path("road/context", RoadContextView.as_view(), name="road_context"),
]
