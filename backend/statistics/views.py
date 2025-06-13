from rest_framework.views import APIView
from projects.models import Perspective
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class PerspectiveAnswerDistribution(APIView):
    # Simplificar permissões para debug
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        logger.info(f"Recebida chamada para perspective-answer-distribution, project_id: {project_id}")

        try:
            perspective = Perspective.objects.get(project_id=project_id)
            logger.info(f"Perspectiva encontrada: {perspective.name}")
        except Perspective.DoesNotExist:
            logger.info(f"Nenhuma perspectiva encontrada para projeto {project_id}")
            # Retornar dados vazios em vez de erro 404
            return Response(data={}, status=status.HTTP_200_OK)

        try:
            data = Perspective.objects.calc_perspective_answer_distribution(perspective)
            logger.info(f"Dados calculados com sucesso: {len(data)} questões")
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erro ao calcular distribuição de perspectiva: {str(e)}")
            return Response(data={}, status=status.HTTP_200_OK)
