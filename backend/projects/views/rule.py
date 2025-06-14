from django.conf import settings
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime

from projects.models import (
    Project,
    AnnotationRuleType,
    AnnotationRule,
    VotingCofiguration,
    AnnotationRuleAnswers,
    Member
)
from projects.permissions import IsProjectAdmin, IsProjectMember, IsAnnotatorForVoting
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
    permission_classes = [IsAuthenticated & IsAnnotatorForVoting]

    def create(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        # Verificar se o usuário é realmente um anotador do projeto
        try:
            member = Member.objects.get(
                project_id=project_id, 
                user=request.user,
                role__name=settings.ROLE_ANNOTATOR
            )
        except Member.DoesNotExist:
            return Response({
                'detail': 'Apenas anotadores podem votar nas regras de anotação.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar se já votou nesta regra
        annotation_rule_id = request.data.get('annotation_rule')
        if annotation_rule_id:
            existing_vote = AnnotationRuleAnswers.objects.filter(
                annotation_rule_id=annotation_rule_id,
                member=member
            ).exists()
            
            if existing_vote:
                return Response({
                    'detail': 'Você já votou nesta regra de anotação.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se a regra pertence ao projeto
        try:
            annotation_rule = AnnotationRule.objects.get(
                id=annotation_rule_id,
                project_id=project_id
            )
        except AnnotationRule.DoesNotExist:
            return Response({
                'detail': 'Regra de anotação não encontrada neste projeto.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar se a votação ainda está ativa
        voting_config = annotation_rule.voting_configuration
        if voting_config.is_closed:
            return Response({
                'detail': 'Esta votação já foi fechada.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se a regra já foi finalizada
        if annotation_rule.is_finalized:
            return Response({
                'detail': 'Esta regra já foi finalizada.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se a votação está dentro do período definido
        current_time = timezone.now()
        
        if current_time < voting_config.begin_date:
            return Response({
                'detail': f'Esta votação ainda não começou. Início: {voting_config.begin_date.strftime("%d/%m/%Y %H:%M")}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if current_time > voting_config.end_date:
            return Response({
                'detail': f'Esta votação já expirou. Fim: {voting_config.end_date.strftime("%d/%m/%Y %H:%M")}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Garantir que o member no request data seja o member autenticado
        request.data['member'] = member.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule_answer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(AnnotationRuleAnswersSerializer(rule_answer).data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
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