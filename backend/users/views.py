from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer
from projects.permissions import IsProjectAdmin


class Me(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class Users(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("username",)


class UserCreation(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        is_superuser = self.request.data.get("is_superuser", False)
        is_staff = self.request.data.get("is_staff", False)
        first_name = self.request.data.get("first_name", "")  
        last_name = self.request.data.get("last_name", "") 

        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user
    
class UserEdit(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if request.user == user:
            return Response(
                {"detail": "You cannot edit your own account."},
                status=status.HTTP_403_FORBIDDEN
            )

        name = request.data.get("name")
        password = request.data.get("password")

        if name:
            user.username = name
        if password:
            user.set_password(password) 

        user.save()

        return Response({"detail": "User updated successfully."}, status=status.HTTP_200_OK)


class UserDeletion(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def delete(self, request, *args, **kwargs):
        # Obtém os usuários a partir dos IDs passados na requisição
        user_ids = request.data.get('user_ids', [])
        
        
        # Se apenas um usuário for excluído, obtém o usuário
        user = self.get_object()

        if request.user == user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.delete()  # Exclui o usuário
        return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)