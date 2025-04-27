from django.conf import settings
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.mail import send_mail

from projects.models import (
    Project,
    AnnotationRuleType,
    AnnotationRule,
    VotingCofiguration,
    AnnotationRuleAnswers,
    Member
)
from projects.permissions import IsProjectAdmin, IsProjectMember
from projects.serializers import (
    AnnotationRuleTypeSerializer,
    AnnotationRuleSerializer,
    VotingCofigurationSerializer,
    AnnotationRuleAnswersSerializer,
)

class AnnotationRuleTypes(generics.ListAPIView):
    queryset = AnnotationRuleType.objects.all()
    serializer_class = AnnotationRuleTypeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("annotation_rule_type",)

class AnnotationRuleTypeCreation(generics.CreateAPIView):
    queryset = AnnotationRuleType.objects.all()
    serializer_class = AnnotationRuleTypeSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['project_id'])

class AnnotationRules(generics.ListAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("description",)

    def get_queryset(self):
        return AnnotationRule.objects.filter(project_id=self.kwargs['project_id'])

class AnnotationRuleCreation(generics.CreateAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['project_id'])

class VotingConfigurations(generics.ListAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("voting_threshold",)

    def get_queryset(self):
        return VotingCofiguration.objects.filter(project_id=self.kwargs['project_id'])

class VotingConfigurationCreation(generics.CreateAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_config = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(VotingCofigurationSerializer(vote_config).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['project_id'], created_by=self.request.user)

class AnnotationRuleAnswersList(generics.ListAPIView):
    serializer_class = AnnotationRuleAnswersSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ['annotation_rule']
    search_fields = ("member__user__username", "answer")

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        annotation_rule_id = self.request.query_params.get('annotation_rule')
        return AnnotationRuleAnswers.objects.filter(
            annotation_rule__project_id=project_id,
            annotation_rule_id=annotation_rule_id
        )

class AnnotationRuleAnswersCreation(generics.CreateAPIView):
    serializer_class = AnnotationRuleAnswersSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule_answer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(AnnotationRuleAnswersSerializer(rule_answer).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        queryset = AnnotationRuleAnswers.objects.all()
        serializer.save()

class AnnotationRuleTypeDetail(RetrieveAPIView):
    queryset = AnnotationRuleType.objects.all()
    serializer_class = AnnotationRuleTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'annotation_rule_type_id'

class AnnotationRuleDetail(RetrieveUpdateAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    lookup_url_kwarg = 'annotation_rule_id'

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

class VotingConfigurationDetail(RetrieveAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'voting_configuration_id'

class AnnotationRuleAnswerDetail(RetrieveAPIView):
    serializer_class = AnnotationRuleAnswersSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'annotation_rule_answer_id'