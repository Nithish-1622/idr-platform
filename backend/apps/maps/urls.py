from django.urls import path

from .views import MapLookupView, MapPackageDetailView, MapPackageListView

app_name = "maps"

urlpatterns = [
    path("maps/", MapPackageListView.as_view(), name="list"),
    path("maps/lookup/", MapLookupView.as_view(), name="lookup"),
    path("maps/<uuid:pk>/", MapPackageDetailView.as_view(), name="detail"),
]
