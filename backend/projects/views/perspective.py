from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from projects.models import Answer, Perspective, Question
from projects.permissions import IsProjectAdmin
from projects.serializers import (
    AnswerSerializer,
    PerspectiveSerializer,
    QuestionSerializer,
)


class Perspectives(generics.ListAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("members__user__username",)


class PerspectiveCreation(generics.CreateAPIView):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            perspective = self.perform_create(serializer)

            questions_data = request.data.get("questions", [])
            for question_data in questions_data:
                question_data["perspective"] = perspective.id
                question_serializer = QuestionSerializer(data=question_data)
                question_serializer.is_valid(raise_exception=True)
                question_serializer.save()

            return Response(PerspectiveSerializer(perspective).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()


class Answers(generics.ListAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("question__id", "member__user__username", "answer")


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
