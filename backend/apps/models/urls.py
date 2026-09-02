from django.urls import path

from .views import (
    LatestActiveModelView,
    LatestModelContractView,
    ModelApproveView,
    ModelContractDetailView,
    ModelListView,
    ModelPublishView,
)

app_name = "models"

urlpatterns = [
    path("models/", ModelListView.as_view(), name="list"),
    path("models/latest/", LatestActiveModelView.as_view(), name="latest"),
    path("models/latest/contract/", LatestModelContractView.as_view(), name="latest_contract"),
    path(
        "models/<uuid:version_id>/contract/",
        ModelContractDetailView.as_view(),
        name="contract_detail",
    ),
    path(
        "models/<uuid:version_id>/approve/", ModelApproveView.as_view(), name="approve"
    ),
    path(
        "models/<uuid:version_id>/publish/", ModelPublishView.as_view(), name="publish"
    ),
]
