from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_device_sync_status_service, get_effective_config_service


class ConfigurationListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        device_key = request.query_params.get("device_key")
        configs = get_effective_config_service(device_key)
        return Response(configs, status=status.HTTP_200_OK)


class DeviceSyncCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: dict})
    def get(self, request):
        device_key = request.query_params.get("device_key", "")
        platform = request.query_params.get("platform", "ANDROID")
        sync_status = get_device_sync_status_service(device_key, platform)
        return Response(sync_status, status=status.HTTP_200_OK)
