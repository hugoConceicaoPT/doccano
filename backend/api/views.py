from celery.result import AsyncResult
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import logging

from labels.models import DatasetReview
from labels.serializers import DatasetReviewSerializer
from examples.models import Example

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
            
            # Extrair dados necessários
            dataset_id = review_data.get('dataset_id')
            dataset_evaluation = review_data.get('dataset_evaluation', {})
            label_agreements = review_data.get('label_agreements', [])
            
            if not dataset_id:
                return Response(
                    {"error": "dataset_id é obrigatório"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar se o exemplo existe
            try:
                example = Example.objects.get(id=dataset_id)
            except Example.DoesNotExist:
                return Response(
                    {"error": f"Exemplo com ID {dataset_id} não encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Criar ou atualizar a revisão do dataset
            dataset_review, created = DatasetReview.objects.update_or_create(
                example=example,
                user=request.user,
                defaults={
                    'is_approved': dataset_evaluation.get('approved', True),
                    'comment': dataset_evaluation.get('comment', ''),
                    'label_agreements': label_agreements
                }
            )
            
            # Serializar a resposta
            serializer = DatasetReviewSerializer(dataset_review)
            
            action = "criada" if created else "atualizada"
            logger.info(f"Dataset review {action} com sucesso: ID {dataset_review.id}")
            
            return Response(
                {
                    "id": dataset_review.id,
                    "message": f"Revisão {action} com sucesso",
                    "reviewed_by": request.user.id,
                    "status": "success",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
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


class DatasetReviewListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Endpoint para listar revisões de datasets
        """
        try:
            # Filtros opcionais
            project_id = request.query_params.get('project_id')
            is_approved = request.query_params.get('is_approved')
            user_id = request.query_params.get('user_id')
            
            # Query base
            queryset = DatasetReview.objects.all()
            
            # Aplicar filtros
            if project_id:
                queryset = queryset.filter(example__project_id=project_id)
            
            if is_approved is not None:
                if is_approved.lower() == 'true':
                    queryset = queryset.filter(is_approved=True)
                elif is_approved.lower() == 'false':
                    queryset = queryset.filter(is_approved=False)
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            # Ordenar por data de criação (mais recentes primeiro)
            queryset = queryset.order_by('-created_at')
            
            # Serializar dados
            serializer = DatasetReviewSerializer(queryset, many=True)
            
            return Response(
                {
                    "count": queryset.count(),
                    "results": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error listing dataset reviews: {str(e)}")
            return Response(
                {
                    "error": "Erro interno do servidor",
                    "detail": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
