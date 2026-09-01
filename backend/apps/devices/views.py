from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsEngineerRole

from .models import Device
from .serializers import (
    DeviceDetailSerializer,
    DeviceHeartbeatSerializer,
    DeviceRegistrationSerializer,
)
from .services import register_device_service, update_device_heartbeat_service


class DeviceRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=DeviceRegistrationSerializer, responses={201: DeviceDetailSerializer}
    )
    def post(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = register_device_service(serializer.validated_data)
        return Response(
            DeviceDetailSerializer(device).data, status=status.HTTP_201_CREATED
        )


class DeviceListView(APIView):
    permission_classes = [IsEngineerRole]

    @extend_schema(responses={200: DeviceDetailSerializer(many=True)})
    def get(self, request):
        devices = Device.objects.all()
        platform = request.query_params.get("platform")
        if platform:
            devices = devices.filter(platform=platform)

        paginator = (
            request.settings_namespace
            if hasattr(request, "settings_namespace")
            else None
        )
        page = (
            self.paginate_queryset(devices)
            if hasattr(self, "paginate_queryset")
            else None
        )
        serializer = DeviceDetailSerializer(devices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeviceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: DeviceDetailSerializer})
    def get(self, request, pk):
        try:
            device = Device.objects.get(pk=pk)
        except Device.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "DEVICE_NOT_FOUND",
                        "message": "Device not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DeviceDetailSerializer(device).data)


class DeviceHeartbeatView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=DeviceHeartbeatSerializer, responses={200: DeviceDetailSerializer}
    )
    def post(self, request, pk):
        try:
            device = Device.objects.get(pk=pk)
        except Device.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "DEVICE_NOT_FOUND",
                        "message": "Device not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DeviceHeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = update_device_heartbeat_service(device, serializer.validated_data)
        return Response(DeviceDetailSerializer(device).data, status=status.HTTP_200_OK)
