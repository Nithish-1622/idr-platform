from django.urls import path

from .views import (
    DeviceDetailView,
    DeviceHeartbeatView,
    DeviceListView,
    DeviceRegisterView,
)

app_name = "devices"

urlpatterns = [
    path("devices/register/", DeviceRegisterView.as_view(), name="register"),
    path("devices/", DeviceListView.as_view(), name="list"),
    path("devices/<uuid:pk>/", DeviceDetailView.as_view(), name="detail"),
    path(
        "devices/<uuid:pk>/heartbeat/", DeviceHeartbeatView.as_view(), name="heartbeat"
    ),
]
