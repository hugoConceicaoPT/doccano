from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from examples.models import Context
from examples.serializers import ContextoSerializer


class ContextList(generics.ListCreateAPIView):
    serializer_class = ContextoSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Context.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class ContextDetail(generics.RetrieveDestroyAPIView):
    queryset = Context.objects.all()
    serializer_class = ContextoSerializer
    permission_classes = [IsAuthenticated]
 