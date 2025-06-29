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
import pytz
from django.db import DatabaseError, OperationalError
import logging

from projects.models import (
    Project,
    AnnotationRule,
    VotingCofiguration,
    AnnotationRuleAnswers,
    Member
)
from projects.permissions import IsProjectAdmin, IsProjectMember, IsAnnotatorForVoting
from projects.serializers import (
    AnnotationRuleSerializer,
    VotingCofigurationSerializer,
    AnnotationRuleAnswersSerializer,
)

logger = logging.getLogger(__name__)

def check_and_finalize_expired_votings(project_id):
    """
    Verifica configurações de votação expiradas e finaliza automaticamente
    as regras não finalizadas dessas configurações.
    """
    try:
        current_time = timezone.now()
        
        # Find active configurations that have already expired
        expired_configs = VotingCofiguration.objects.filter(
            project_id=project_id,
            is_closed=False,
            end_date__lt=current_time
        )
        
        for config in expired_configs:
            logger.info(f"Voting configuration {config.id} expired on {config.end_date}")
            
            # Find unfinalized rules from this configuration
            unfinalized_rules = AnnotationRule.objects.filter(
                voting_configuration=config,
                is_finalized=False
            )
            
            for rule in unfinalized_rules:
                # Calcular resultado baseado nos votos recebidos
                votes_for = AnnotationRuleAnswers.objects.filter(
                    annotation_rule=rule,
                    answer=True
                ).count()
                
                votes_against = AnnotationRuleAnswers.objects.filter(
                    annotation_rule=rule,
                    answer=False
                ).count()
                
                total_votes = votes_for + votes_against
                
                if total_votes == 0:
                    final_result = "No votes"
                elif votes_for > votes_against:
                    final_result = "Approved"
                elif votes_against > votes_for:
                    final_result = "Rejected"
                else:
                    final_result = "Tie"
                
                # Finalizar a regra
                rule.is_finalized = True
                rule.final_result = final_result
                rule.save()
                
                logger.info(f"Rule {rule.id} automatically finalized by expiration: {final_result} ({votes_for} for, {votes_against} against, {total_votes} total)")
            
            # Fechar a configuração de votação
            config.is_closed = True
            config.save()
            
            logger.info(f"Voting configuration {config.id} automatically closed by expiration")
            
    except Exception as e:
        logger.error(f"Error checking/finalizing expired votings in project {project_id}: {str(e)}")

class AnnotationRules(generics.ListAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        check_and_finalize_expired_votings(project_id)
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

class UnvotedAnnotationRules(generics.ListAPIView):
    """
    Returns only annotation rules that the current user has not yet voted on
    """
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        user = self.request.user
        
        # Check and finalize expired configurations
        check_and_finalize_expired_votings(project_id)
        
        # Obter o membro atual
        try:
            member = Member.objects.get(
                project_id=project_id,
                user=user
            )
        except Member.DoesNotExist:
            return AnnotationRule.objects.none()
        
        # Obter IDs das regras já votadas pelo usuário
        voted_rule_ids = AnnotationRuleAnswers.objects.filter(
            member=member,
            annotation_rule__project_id=project_id
        ).values_list('annotation_rule_id', flat=True)
        
        # Retornar apenas regras não votadas, não finalizadas e de votações ativas
        return AnnotationRule.objects.filter(
            project_id=project_id,
            is_finalized=False,
            voting_configuration__is_closed=False
        ).exclude(
            id__in=voted_rule_ids
        ).select_related('voting_configuration')

    def list(self, request, *args, **kwargs):
        """
        Override to add extra information about voting status
        """
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            # Adicionar informações sobre votações ativas
            project_id = self.kwargs['project_id']
            active_configs = VotingCofiguration.objects.filter(
                project_id=project_id,
                is_closed=False
            )
            
            current_time = timezone.now()
            active_voting_info = []
            
            for config in active_configs:
                is_active = (current_time >= config.begin_date and 
                            current_time <= config.end_date)
                
                active_voting_info.append({
                    'id': config.id,
                    'version': config.version,
                    'begin_date': config.begin_date,
                    'end_date': config.end_date,
                    'is_active': is_active,
                    'is_expired': current_time > config.end_date,
                    'not_started': current_time < config.begin_date
                })
            
            return Response({
                'rules': serializer.data,
                'active_votings': active_voting_info,
                'total_unvoted_rules': len(serializer.data)
            })
            
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Database error when listing unvoted rules: {str(e)}")
            return Response({
                'detail': 'Database connection error. The database is temporarily unavailable. Please try again in a few moments.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Unexpected error when listing unvoted rules: {str(e)}")
            return Response({
                'detail': 'Internal server error. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AnnotationRuleCreation(generics.CreateAPIView):
    queryset = AnnotationRule.objects.all()
    serializer_class = AnnotationRuleSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs['project_id'])

class VotingConfigurations(generics.ListAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("voting_threshold",)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        check_and_finalize_expired_votings(project_id)
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
        
        # Check and finalize expired configurations before creating new one
        check_and_finalize_expired_votings(project_id)
        
        active_configs = VotingCofiguration.objects.filter(project_id=project_id, is_closed=False)
        
        if active_configs.exists():
            active_config = active_configs.first()
            all_rules = AnnotationRule.objects.filter(voting_configuration=active_config)
            
            if not all_rules.exists() or all(rule.is_finalized for rule in all_rules):
                active_config.is_closed = True
                active_config.save()
            else:
                return Response({
                    'detail': 'Cannot configure a new voting because there is an active voting with unfinalized rules.'
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
    permission_classes = [IsAuthenticated & IsProjectMember]
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
        
        try:
            # Check if the user is really an annotator of the project
            try:
                member = Member.objects.get(
                    project_id=project_id, 
                    user=request.user,
                    role__name=settings.ROLE_ANNOTATOR
                )
            except Member.DoesNotExist:
                return Response({
                    'detail': 'Only annotators can vote on annotation rules.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if already voted on this rule
            annotation_rule_id = request.data.get('annotation_rule')
            if annotation_rule_id:
                existing_vote = AnnotationRuleAnswers.objects.filter(
                    annotation_rule_id=annotation_rule_id,
                    member=member
                ).exists()
                
                if existing_vote:
                    return Response({
                        'detail': 'You have already voted on this annotation rule.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the rule belongs to the project
            try:
                annotation_rule = AnnotationRule.objects.get(
                    id=annotation_rule_id,
                    project_id=project_id
                )
            except AnnotationRule.DoesNotExist:
                return Response({
                    'detail': 'Annotation rule not found in this project.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if voting is still active
            voting_config = annotation_rule.voting_configuration
            if voting_config.is_closed:
                return Response({
                    'detail': 'This voting has already been closed.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the rule has already been finalized
            if annotation_rule.is_finalized:
                return Response({
                    'detail': 'This rule has already been finalized.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if voting is within the defined period
            current_time = timezone.now()
            
            # Convert to Lisbon timezone for display
            lisbon_tz = pytz.timezone('Europe/Lisbon')
            
            if current_time < voting_config.begin_date:
                begin_local = voting_config.begin_date.astimezone(lisbon_tz)
                return Response({
                    'detail': f'This voting has not started yet. Start: {begin_local.strftime("%d/%m/%Y %H:%M")}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if current_time > voting_config.end_date:
                end_local = voting_config.end_date.astimezone(lisbon_tz)
                return Response({
                    'detail': f'This voting has already expired. End: {end_local.strftime("%d/%m/%Y %H:%M")}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ensure that the member in request data is the authenticated member
            request.data['member'] = member.id
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            rule_answer = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(AnnotationRuleAnswersSerializer(rule_answer).data, status=status.HTTP_201_CREATED, headers=headers)
            
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Database error when creating vote: {str(e)}")
            return Response({
                'detail': 'Database connection error. The database is temporarily unavailable. Please try again in a few moments.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Unexpected error when creating vote: {str(e)}")
            return Response({
                'detail': 'Internal server error. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        # Save the vote
        rule_answer = serializer.save()
        
        # Check if all project annotators have already voted on this rule
        project_id = self.kwargs['project_id']
        annotation_rule = rule_answer.annotation_rule
        
        try:
            # Get all project annotators
            project_annotators = Member.objects.filter(
                project_id=project_id,
                role__name=settings.ROLE_ANNOTATOR
            )
            total_annotators = project_annotators.count()
            
            logger.info(f"Total annotators in project {project_id}: {total_annotators}")
            
            # Check how many annotators have already voted on this rule
            votes_count = AnnotationRuleAnswers.objects.filter(
                annotation_rule=annotation_rule
            ).count()
            
            logger.info(f"Votes received for rule {annotation_rule.id}: {votes_count}")
            
            if total_annotators > 0 and votes_count >= total_annotators:
                logger.info(f"All annotators ({total_annotators}) voted on rule {annotation_rule.id}")
                
                # Calculate voting result
                votes_for = AnnotationRuleAnswers.objects.filter(
                    annotation_rule=annotation_rule,
                    answer=True
                ).count()
                
                votes_against = AnnotationRuleAnswers.objects.filter(
                    annotation_rule=annotation_rule,
                    answer=False
                ).count()
                
                # Determine result based on majority
                if votes_for > votes_against:
                    final_result = "Approved"
                elif votes_against > votes_for:
                    final_result = "Rejected"
                else:
                    final_result = "Tie"
                
                logger.info(f"Voting result for rule {annotation_rule.id}: {final_result} ({votes_for} for, {votes_against} against)")
                
                # Finalize the rule
                annotation_rule.is_finalized = True
                annotation_rule.final_result = final_result
                annotation_rule.save()
                
                logger.info(f"Rule {annotation_rule.id} automatically finalized")
                
                # Check if all rules in the voting configuration are finalized
                voting_config = annotation_rule.voting_configuration
                all_rules = AnnotationRule.objects.filter(voting_configuration=voting_config)
                
                all_finalized = True
                for rule in all_rules:
                    if not rule.is_finalized:
                        all_finalized = False
                        break
                
                if all_finalized:
                    voting_config.is_closed = True
                    voting_config.save()
                    logger.info(f"Voting configuration {voting_config.id} automatically closed - all rules finalized")
                
        except Exception as e:
            logger.error(f"Error checking/finalizing automatic voting: {str(e)}")
        
        return rule_answer

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
                response.data['message'] = 'All rules in this voting have been finalized. The voting was automatically closed.'
        
        return response

class VotingConfigurationDetail(RetrieveAPIView):
    queryset = VotingCofiguration.objects.all()
    serializer_class = VotingCofigurationSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    lookup_url_kwarg = 'voting_configuration_id'

class AnnotationRuleAnswerDetail(RetrieveAPIView):
    serializer_class = AnnotationRuleAnswersSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    lookup_url_kwarg = 'annotation_rule_answer_id'