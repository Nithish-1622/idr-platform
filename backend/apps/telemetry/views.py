from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAnalystRole

from .models import TelemetrySession
from .serializers import TelemetryBatchIngestSerializer, TelemetrySessionSerializer
from .services import ingest_telemetry_batch_service


class TelemetryBatchIngestView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=TelemetryBatchIngestSerializer, responses={201: dict, 200: dict}
    )
    def post(self, request):
        serializer = TelemetryBatchIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            batch, created = ingest_telemetry_batch_service(serializer.validated_data)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(
                {
                    "message": "Telemetry batch processed successfully.",
                    "batch_id": batch.batch_id,
                    "points_ingested": batch.point_count,
                    "duplicate_ignored": not created,
                },
                status=status_code,
            )
        except ValueError as e:
            return Response(
                {
                    "error": {
                        "code": "TELEMETRY_INGESTION_ERROR",
                        "message": str(e),
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class TelemetrySessionListView(APIView):
    permission_classes = [IsAnalystRole]

    @extend_schema(responses={200: TelemetrySessionSerializer(many=True)})
    def get(self, request):
        sessions = TelemetrySession.objects.select_related("device").all()
        return Response(TelemetrySessionSerializer(sessions, many=True).data)
