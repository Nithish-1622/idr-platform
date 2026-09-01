from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MapPackage
from .serializers import MapPackageSerializer
from .services import find_maps_for_coordinates


class MapPackageListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: MapPackageSerializer(many=True)})
    def get(self, request):
        packages = MapPackage.objects.filter(is_active=True)
        region = request.query_params.get("region_code")
        if region:
            packages = packages.filter(region_code=region)
        return Response(MapPackageSerializer(packages, many=True).data)


class MapPackageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: MapPackageSerializer})
    def get(self, request, pk):
        try:
            package = MapPackage.objects.get(pk=pk)
        except MapPackage.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "MAP_PACKAGE_NOT_FOUND",
                        "message": "Map package not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MapPackageSerializer(package).data)


class MapLookupView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: MapPackageSerializer(many=True)})
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", 0.0))
            lng = float(request.query_params.get("lng", 0.0))
        except ValueError:
            return Response(
                {
                    "error": {
                        "code": "INVALID_COORDINATES",
                        "message": "Latitude and longitude must be numbers.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        matches = find_maps_for_coordinates(lat, lng)
        return Response(MapPackageSerializer(matches, many=True).data)
