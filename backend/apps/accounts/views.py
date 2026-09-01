from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterUserSerializer, UserSerializer
from .services import generate_tokens_for_user, register_user_service


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterUserSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user_service(serializer.validated_data)
        tokens = generate_tokens_for_user(user)
        response_data = UserSerializer(user).data
        response_data["tokens"] = tokens
        return Response(response_data, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
