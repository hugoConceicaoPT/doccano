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
    AnnotationRule,
    VotingCofiguration,
    AnnotationRuleAnswers,
    Member
)
from projects.permissions import IsProjectAdmin, IsProjectMember
from projects.serializers import (
    AnnotationRuleSerializer,
    VotingCofigurationSerializer,
    AnnotationRuleAnswersSerializer,
)

class AnnotationRules(generics.ListAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        self.check_and_close_completed_configs(project_id)
        return AnnotationRule.objects.filter(project_id=project_id)
    
    def check_and_close_completed_configs(self, project_id):
        active_configs = VotingCofiguration.objects.filter(
            project_id=project_id, 
            is_closed=False
        )
        
        for config in active_configs:
            rules = AnnotationRule.objects.filter(voting_configuration=config)
            
            if not rules.exists():
                continue
                
            all_finalized = all(rule.is_finalized for rule in rules)
            
            if all_finalized:
                config.is_closed = True
                config.save()

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
        project_id = self.kwargs['project_id']
        self.check_and_close_completed_configs(project_id)
        return VotingCofiguration.objects.filter(project_id=project_id)
    
    def check_and_close_completed_configs(self, project_id):
        active_configs = VotingCofiguration.objects.filter(
            project_id=project_id, 
            is_closed=False
        )
        
        for config in active_configs:
            rules = AnnotationRule.objects.filter(voting_configuration=config)
            
            if not rules.exists():
                continue
                
            all_finalized = all(rule.is_finalized for rule in rules)
            
            if all_finalized:
                config.is_closed = True
                config.save()

class VotingConfigurationCreation(generics.CreateAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def create(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        active_configs = VotingCofiguration.objects.filter(project_id=project_id, is_closed=False)
        
        if active_configs.exists():
            active_config = active_configs.first()
            all_rules = AnnotationRule.objects.filter(voting_configuration=active_config)
            
            if not all_rules.exists() or all(rule.is_finalized for rule in all_rules):
                active_config.is_closed = True
                active_config.save()
            else:
                return Response({
                    'detail': 'Não é possível configurar uma nova votação pois existe uma votação ativa com regras não finalizadas.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'version' in request.data:
            version = request.data['version']
            if VotingCofiguration.objects.filter(project_id=project_id, version=version).exists():
                max_version = VotingCofiguration.objects.filter(project_id=project_id).order_by('-version').first()
                if max_version:
                    next_version = max_version.version + 1
                else:
                    next_version = 1
                
                request.data['version'] = next_version
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_config = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(VotingCofigurationSerializer(vote_config).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save(project_id=self.kwargs['project_id'], created_by=self.request.user)

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

class AnnotationRuleDetail(RetrieveUpdateAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    lookup_url_kwarg = 'annotation_rule_id'

    def put(self, request, *args, **kwargs):
        response = self.partial_update(request, *args, **kwargs)
        
        annotation_rule = self.get_object()
        voting_config = annotation_rule.voting_configuration
        
        all_rules = AnnotationRule.objects.filter(voting_configuration=voting_config)
        
        all_finalized = True
        for rule in all_rules:
            if not rule.is_finalized:
                all_finalized = False
                break
        
        if all_finalized and not voting_config.is_closed:
            voting_config.is_closed = True
            voting_config.save()
            
            if isinstance(response.data, dict):
                response.data['message'] = 'Todas as regras desta votação foram finalizadas. A votação foi fechada automaticamente.'
        
        return response

class VotingConfigurationDetail(RetrieveAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'voting_configuration_id'

class AnnotationRuleAnswerDetail(RetrieveAPIView):
    serializer_class = AnnotationRuleAnswersSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'annotation_rule_answer_id'