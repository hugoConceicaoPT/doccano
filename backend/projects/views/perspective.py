from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, serializers, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail

from projects.models import (
    Answer,
    Perspective,
    Question,
    Member
)
from projects.serializers import (
    AnswerSerializer,
    PerspectiveSerializer,
    QuestionSerializer,
)


class Perspectives(generics.ListAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("members__user__username",)

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        if project_id:
            return Perspective.objects.filter(project_id=project_id)
        return Perspective.objects.all()


class AllPerspectives(generics.ListAPIView):
    """
    View para retornar todas as perspectivas de todos os projetos
    para permitir reutilização entre projetos
    """
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)


@method_decorator(csrf_exempt, name='dispatch')
class PerspectiveCreation(generics.CreateAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        project_id = request.data.get("project_id")
        

        
        try:
            with transaction.atomic():
                # Verificar se já existe uma perspectiva para este projeto
                try:
                    existing_perspective = Perspective.objects.get(project_id=project_id)
                    
                    # Se existe, atualizar a existente
                    serializer = self.get_serializer(existing_perspective, data=request.data, partial=True)
                    if not serializer.is_valid():
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                    perspective = serializer.save()
                    
                    # Remover perguntas antigas
                    existing_perspective.questions.all().delete()
                    
                except Perspective.DoesNotExist:
                    # Se não existe, criar nova
                    serializer = self.get_serializer(data=request.data)
                    if not serializer.is_valid():
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                    perspective = self.perform_create(serializer)

                # Adicionar novas perguntas
                questions_data = request.data.get("questions", [])
                
                for question_data in questions_data:
                    question_data["perspective"] = perspective.id
                    question_serializer = QuestionSerializer(data=question_data)
                    if not question_serializer.is_valid():
                        return Response(question_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    question_serializer.save()
                    
                # Recarregar a perspectiva para garantir que as perguntas estão incluídas
                perspective.refresh_from_db()
                
                # Usar um serializer mais simples para a resposta
                response_data = {
                    "id": perspective.id,
                    "name": perspective.name,
                    "project_id": perspective.project.id,
                    "created_at": perspective.created_at,
                    "questions": [
                        {
                            "id": q.id,
                            "question": q.question,
                            "answer_type": q.answer_type
                        }
                        for q in perspective.questions.all()
                    ]
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            # Retornar erro genérico
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
     

    def perform_create(self, serializer):
        return serializer.save()


class Answers(generics.ListAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    # Optionally, you can also use filterset_fields for other filtering
    filterset_fields = ['question']
    search_fields = ("question__id", "member__user__username", "answer_text", "answer_option")

    def get_queryset(self):
        queryset = Answer.objects.all()
        # Get the selected question id from query parameters
        question_id = self.request.query_params.get('question_id')
        if question_id:
            queryset = queryset.filter(question__id=question_id)
        return queryset


class AnswerCreation(generics.CreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(AnswerSerializer(answer).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        answer = serializer.save()
        return answer


class Questions(generics.ListAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("perspective__id", "question")


class AnswerNestedSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()

    class Meta:
        model = Answer
        fields = ("id", "answer_text", "member")


class QuestionNestedSerializer(serializers.ModelSerializer):
    answers = AnswerNestedSerializer(many=True, read_only=True, source="answers")

    class Meta:
        model = Question
        fields = ("id", "question", "answer_type", "answers")


class PerspectiveDetailSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        read_only=True
    )

    class Meta:
        model = Perspective
        fields = ("id", "name", "project_id")
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Adicionar questions manualmente para debug
        questions_data = []
        try:
            questions = instance.questions.all()
            for question in questions:
                question_data = {
                    "id": question.id,
                    "question": question.question,
                    "answer_type": question.answer_type,
                    "answers": []
                }
                questions_data.append(question_data)
        except Exception as e:
            print(f"Erro ao carregar questions: {e}")
        
        data["questions"] = questions_data
        return data


class PerspectiveDetail(RetrieveAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveDetailSerializer
    permission_classes = [IsAuthenticated]
