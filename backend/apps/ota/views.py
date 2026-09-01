from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OTACheckRequestSerializer
from .services import check_for_updates_service


class OTACheckView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=OTACheckRequestSerializer, responses={200: list})
    def post(self, request):
        serializer = OTACheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        updates = check_for_updates_service(
            platform=data["platform"],
            app_version=data["app_version"],
            current_model_version=data.get("current_model_version", ""),
            current_map_version=data.get("current_map_version", ""),
        )
        return Response({"available_updates": updates}, status=status.HTTP_200_OK)
