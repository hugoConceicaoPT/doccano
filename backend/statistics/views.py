from rest_framework.views import APIView
from projects.models import Perspective
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class PerspectiveAnswerDistribution(APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]

        try:
            perspective = Perspective.objects.get(project_id=project_id)
        except Perspective.DoesNotExist:
            return Response({"detail": "Perspective not found."}, status=status.HTTP_404_NOT_FOUND)

        data = Perspective.objects.calc_perspective_answer_distribution(perspective)
        return Response(data=data, status=status.HTTP_200_OK)
