from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsEngineerRole

from .models import Dataset
from .serializers import DatasetSerializer


class DatasetListView(APIView):
    permission_classes = [IsEngineerRole]

    @extend_schema(responses={200: DatasetSerializer(many=True)})
    def get(self, request):
        datasets = Dataset.objects.all()
        return Response(DatasetSerializer(datasets, many=True).data)

    @extend_schema(request=DatasetSerializer, responses={201: DatasetSerializer})
    def post(self, request):
        serializer = DatasetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save()
        return Response(DatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)


class DatasetDetailView(APIView):
    permission_classes = [IsEngineerRole]

    @extend_schema(responses={200: DatasetSerializer})
    def get(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "DATASET_NOT_FOUND",
                        "message": "Dataset not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DatasetSerializer(dataset).data)
