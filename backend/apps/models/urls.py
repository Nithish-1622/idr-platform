from django.urls import path

from .views import (
    LatestActiveModelView,
    ModelApproveView,
    ModelListView,
    ModelPublishView,
)

app_name = "models"

urlpatterns = [
    path("models/", ModelListView.as_view(), name="list"),
    path("models/latest/", LatestActiveModelView.as_view(), name="latest"),
    path(
        "models/<uuid:version_id>/approve/", ModelApproveView.as_view(), name="approve"
    ),
    path(
        "models/<uuid:version_id>/publish/", ModelPublishView.as_view(), name="publish"
    ),
]
