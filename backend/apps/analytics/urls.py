from django.urls import path

from .views import AnalyticsSummaryView, ModelPerformanceAnalyticsView

app_name = "analytics"

urlpatterns = [
    path("analytics/summary/", AnalyticsSummaryView.as_view(), name="summary"),
    path(
        "analytics/model-performance/",
        ModelPerformanceAnalyticsView.as_view(),
        name="model_performance",
    ),
]
