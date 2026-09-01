import logging

import redis
from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthLiveView(APIView):
    """Liveness probe to confirm backend API is responding."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"status": "live", "service": "idr-backend"}, status=status.HTTP_200_OK
        )


class HealthReadyView(APIView):
    """Readiness probe to confirm DB and Redis connections are operational."""

    permission_classes = [AllowAny]

    def get(self, request):
        health = {"database": "unknown", "redis": "unknown", "status": "ready"}
        healthy = True

        # Check Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health["database"] = "ok"
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
            health["database"] = f"error: {str(e)}"
            healthy = False

        # Check Redis
        try:
            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            health["redis"] = "ok"
        except Exception as e:
            logger.warning(f"Redis readiness check warning: {e}")
            health["redis"] = f"warning: {str(e)}"

        status_code = (
            status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        if not healthy:
            health["status"] = "unhealthy"

        return Response(health, status=status_code)
