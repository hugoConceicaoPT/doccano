from celery.result import AsyncResult
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class TaskStatus(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        task = AsyncResult(kwargs["task_id"])
        ready = task.ready()
        error = ready and not task.successful()

        return Response(
            {
                "ready": ready,
                "result": task.result if ready and not error else None,
                "error": {"text": str(task.result)} if error else None,
            }
        )


class DatasetReviewView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        Endpoint para submeter revisões de concordância entre anotadores
        """
        try:
            # Log da revisão recebida
            review_data = request.data
            logger.info(f"Dataset review submitted by user {request.user.id}: {review_data}")
            
            # Aqui poderia ser implementada a lógica para guardar na base de dados
            # Por agora, apenas retornamos sucesso para testar a conectividade
            
            return Response(
                {
                    "id": review_data.get('dataset_id'),
                    "message": "Revisão submetida com sucesso",
                    "reviewed_by": request.user.id,
                    "status": "success"
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error submitting dataset review: {str(e)}")
            return Response(
                {
                    "error": "Erro interno do servidor",
                    "detail": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
