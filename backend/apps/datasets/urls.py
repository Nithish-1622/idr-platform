from django.urls import path

from .views import DatasetDetailView, DatasetListView

app_name = "datasets"

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="list"),
    path("datasets/<uuid:pk>/", DatasetDetailView.as_view(), name="detail"),
]
