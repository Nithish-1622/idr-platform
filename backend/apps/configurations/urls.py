from django.urls import path

from .views import ConfigurationListView, DeviceSyncCheckView

app_name = "configurations"

urlpatterns = [
    path("config/", ConfigurationListView.as_view(), name="list"),
    path("config/sync/", DeviceSyncCheckView.as_view(), name="sync_check"),
]
