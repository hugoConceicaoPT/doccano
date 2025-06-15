from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from labels.models import DatasetReview
from labels.serializers import DatasetReviewSerializer
from examples.models import Example

logger = logging.getLogger(__name__)

class DatasetReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
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
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        queryset = DatasetReview.objects.filter(example__project_id=project_id)
        serializer = DatasetReviewSerializer(queryset, many=True)
        return Response(serializer.data) 