from django.urls import path

from .views import OTACheckView

app_name = "ota"

urlpatterns = [
    path("ota/check/", OTACheckView.as_view(), name="check"),
]
