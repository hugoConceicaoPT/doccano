from dj_rest_auth.registration.serializers import RegisterSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from projects.models import Member
from perspectives.models import Perspective
from .serializers import PerspectiveSerializer
from projects.permissions import IsProjectAdmin

class Perspectives(generics.ListAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("member",)

class PerspectiveCreation(generics.CreateAPIView):
    queryset = Perspective.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        member = Member.objects.get(user=self.request.user)  # Obtém o Member associado ao usuário autenticado
        perspective = serializer.save(member=member)  # Associa o Member antes de salvar
        return perspective