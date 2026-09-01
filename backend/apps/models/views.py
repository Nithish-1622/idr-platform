from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsEngineerRole

from .models import Deployment, MLModel, ModelVersion
from .serializers import DeploymentSerializer, MLModelSerializer, ModelVersionSerializer
from .services import approve_model_version_service, publish_model_version_service


class ModelListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MLModelSerializer(many=True)})
    def get(self, request):
        models = MLModel.objects.all()
        return Response(MLModelSerializer(models, many=True).data)

    @extend_schema(request=MLModelSerializer, responses={201: MLModelSerializer})
    def post(self, request):
        serializer = MLModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        model = serializer.save()
        return Response(MLModelSerializer(model).data, status=status.HTTP_201_CREATED)


class LatestActiveModelView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: ModelVersionSerializer})
    def get(self, request):
        platform = request.query_params.get("platform", "ALL")
        deployment = (
            Deployment.objects.filter(
                is_active=True, target_platform__in=[platform, "ALL"]
            )
            .select_related("model_version", "model_version__artifact")
            .first()
        )

        if not deployment:
            return Response(
                {
                    "error": {
                        "code": "MODEL_NOT_FOUND",
                        "message": "No active model deployment available.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ModelVersionSerializer(deployment.model_version).data)


class ModelApproveView(APIView):
    permission_classes = [IsEngineerRole]

    @extend_schema(responses={200: ModelVersionSerializer})
    def post(self, request, version_id):
        try:
            model_version = ModelVersion.objects.get(pk=version_id)
            updated = approve_model_version_service(model_version)
            return Response(ModelVersionSerializer(updated).data)
        except (ModelVersion.DoesNotExist, ValueError) as e:
            return Response(
                {
                    "error": {
                        "code": "MODEL_APPROVAL_ERROR",
                        "message": str(e),
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ModelPublishView(APIView):
    permission_classes = [IsEngineerRole]

    @extend_schema(responses={201: DeploymentSerializer})
    def post(self, request, version_id):
        try:
            model_version = ModelVersion.objects.get(pk=version_id)
            target_platform = request.data.get("target_platform", "ALL")
            deployment = publish_model_version_service(model_version, target_platform)
            return Response(
                DeploymentSerializer(deployment).data, status=status.HTTP_201_CREATED
            )
        except (ModelVersion.DoesNotExist, ValueError) as e:
            return Response(
                {
                    "error": {
                        "code": "MODEL_PUBLISH_ERROR",
                        "message": str(e),
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
