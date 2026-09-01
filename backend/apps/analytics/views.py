from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAnalystRole

from .services import get_model_performance_analytics, get_telemetry_analytics_summary


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAnalystRole]

    @extend_schema(responses={200: dict})
    def get(self, request):
        summary = get_telemetry_analytics_summary()
        return Response(summary, status=status.HTTP_200_OK)


class ModelPerformanceAnalyticsView(APIView):
    permission_classes = [IsAnalystRole]

    @extend_schema(responses={200: dict})
    def get(self, request):
        performance = get_model_performance_analytics()
        return Response(performance, status=status.HTTP_200_OK)
