from django.urls import path

from .views import TelemetryBatchIngestView, TelemetrySessionListView

app_name = "telemetry"

urlpatterns = [
    path("telemetry/batch/", TelemetryBatchIngestView.as_view(), name="batch_ingest"),
    path(
        "telemetry/sessions/", TelemetrySessionListView.as_view(), name="session_list"
    ),
]
