from django.shortcuts import render
import csv
import io
import logging
from django.http import HttpResponse
from django.db.utils import DatabaseError, OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

logger = logging.getLogger(__name__)

# Imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly
from .serializers import (
    AnnotatorReportFilterSerializer,
    AnnotatorReportResponseSerializer,
    AnnotationReportFilterSerializer,
    AnnotationReportResponseSerializer
)
from .services import AnnotatorReportService, AnnotationReportService


class AnnotatorReportView(APIView):
    """
    View para gerar relatório sobre anotadores com vários filtros
    """
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    @swagger_auto_schema(
        operation_description="Gerar relatório sobre anotadores com filtros",
        query_serializer=AnnotatorReportFilterSerializer,
        responses={
            200: AnnotatorReportResponseSerializer,
            400: "Parâmetros inválidos",
            403: "Sem permissão para aceder aos projetos especificados"
        },
        manual_parameters=[
            openapi.Parameter(
                'project_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos projetos (separados por vírgula)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'user_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos utilizadores (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Data de início (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Data de fim (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'label_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos rótulos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perspectivas (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'dataset_names',
                openapi.IN_QUERY,
                description="Lista de nomes dos datasets (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_question_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perguntas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_answer_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das respostas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Gerar relatório sobre anotadores"""
        
        # Processar parâmetros da query string
        query_params_source = getattr(request, 'query_params', request.GET)
        query_params = self._process_query_params(query_params_source)
        
        # Validar parâmetros
        serializer = AnnotatorReportFilterSerializer(data=query_params)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # Verificar permissões para os projetos especificados
        project_ids = validated_data['project_ids']
        if not self._check_project_permissions(request.user, project_ids):
            return Response(
                {"detail": "Não tem permissão para aceder a alguns dos projetos especificados"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Gerar relatório
            print(f"[DEBUG] Gerando relatório com parâmetros: {validated_data}")
            report_data = AnnotatorReportService.get_report(**validated_data)
            print(f"[DEBUG] Relatório gerado com sucesso: {len(report_data.get('data', []))} anotadores")
            
            # Serializar resposta
            response_serializer = AnnotatorReportResponseSerializer(data=report_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Erro de base de dados ao gerar relatório de anotadores: {str(e)}")
            return Response(
                {"detail": "Database is slow or unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            print(f"[DEBUG] ERRO ao gerar relatório:")
            print(f"[DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[DEBUG] Traceback completo:")
            traceback.print_exc()
            
            logger.error(f"Erro inesperado ao gerar relatório de anotadores: {str(e)}")
            return Response(
                {"detail": f"Erro interno do servidor. Tente novamente mais tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_query_params(self, query_params):
        """Processar parâmetros da query string"""
        processed = {}
        
        # Processar project_ids (obrigatório)
        if 'project_ids' in query_params:
            try:
                processed['project_ids'] = [
                    int(x.strip()) for x in query_params['project_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['project_ids'] = []
        
        # Processar user_ids (opcional)
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                processed['user_ids'] = [
                    int(x.strip()) for x in query_params['user_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['user_ids'] = []
        
        # Processar label_ids (opcional)
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                processed['label_ids'] = [
                    int(x.strip()) for x in query_params['label_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['label_ids'] = []
        
        # Processar perspective_ids (opcional)
        if 'perspective_ids' in query_params and query_params['perspective_ids']:
            try:
                processed['perspective_ids'] = [
                    int(x.strip()) for x in query_params['perspective_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_ids'] = []
        
        # Processar dataset_names (opcional)
        if 'dataset_names' in query_params and query_params['dataset_names']:
            processed['dataset_names'] = [
                x.strip() for x in query_params['dataset_names'].split(',') if x.strip()
            ]
        
        # Processar datas (opcional)
        if 'date_from' in query_params and query_params['date_from']:
            processed['date_from'] = query_params['date_from']
        
        if 'date_to' in query_params and query_params['date_to']:
            processed['date_to'] = query_params['date_to']
        
        # Processar perspective_question_ids (opcional)
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                processed['perspective_question_ids'] = [
                    int(x.strip()) for x in query_params['perspective_question_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_question_ids'] = []
        
        # Processar perspective_answer_ids (opcional)
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                processed['perspective_answer_ids'] = [
                    int(x.strip()) for x in query_params['perspective_answer_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_answer_ids'] = []
        
        return processed

    def _check_project_permissions(self, user, project_ids):
        """Verificar se o utilizador tem permissão para aceder aos projetos"""
        from projects.models import Project, Member
        from roles.models import Role
        from django.conf import settings
        
        # Se for superuser, tem acesso a tudo
        if user.is_superuser:
            return True
        
        # Verificar se é admin ou staff de todos os projetos
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                member = Member.objects.get(project=project, user=user)
                
                # Verificar se tem role de admin ou annotation approver
                admin_role = Role.objects.get(name=settings.ROLE_PROJECT_ADMIN)
                approver_role = Role.objects.get(name=settings.ROLE_ANNOTATION_APPROVER)
                
                if member.role not in [admin_role, approver_role]:
                    return False
                    
            except (Project.DoesNotExist, Member.DoesNotExist, Role.DoesNotExist):
                return False
        
        return True


class AnnotatorReportExportView(APIView):
    """
    View para exportar relatório sobre anotadores em múltiplos formatos
    """
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    


    @swagger_auto_schema(
        operation_description="Exportar relatório sobre anotadores em CSV ou PDF",
        query_serializer=AnnotatorReportFilterSerializer,
        manual_parameters=[
            openapi.Parameter(
                'export_format',
                openapi.IN_QUERY,
                description="Formato de exportação: csv ou pdf",
                type=openapi.TYPE_STRING,
                enum=['csv', 'pdf'],
                default='csv',
                required=False
            ),
            openapi.Parameter(
                'project_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos projetos (separados por vírgula)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'user_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos utilizadores (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Data de início (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Data de fim (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'label_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos rótulos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perspectivas (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'dataset_names',
                openapi.IN_QUERY,
                description="Lista de nomes dos datasets (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_question_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perguntas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_answer_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das respostas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: "Arquivo exportado",
            400: "Parâmetros inválidos",
            403: "Sem permissão para aceder aos projetos especificados"
        }
    )
    def get(self, request, *args, **kwargs):
        """Exportar relatório sobre anotadores"""
        

        # Usar request.GET para compatibilidade com Django padrão e DRF
        query_params_source = getattr(request, 'query_params', request.GET)
        
        # Obter formato de exportação (suportar tanto 'format' quanto 'export_format' para compatibilidade)
        export_format = query_params_source.get('export_format', query_params_source.get('format', 'csv')).lower()
        
        if export_format not in ['csv', 'pdf']:
            return Response(
                {"detail": "Formato inválido. Use: csv ou pdf"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Processar parâmetros da query string (reutilizar lógica da view principal)
        query_params = self._process_query_params(query_params_source)
        
        # Validar parâmetros
        serializer = AnnotatorReportFilterSerializer(data=query_params)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # Verificar permissões para os projetos especificados
        project_ids = validated_data['project_ids']
        if not self._check_project_permissions(request.user, project_ids):
            return Response(
                {"detail": "Não tem permissão para aceder a alguns dos projetos especificados"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Gerar relatório
            print(f"[EXPORT DEBUG] Gerando relatório para exportação com parâmetros: {validated_data}")
            print(f"[EXPORT DEBUG] Formato de exportação: {export_format}")
            report_data = AnnotatorReportService.get_report(**validated_data)
            print(f"[EXPORT DEBUG] Relatório gerado com sucesso: {len(report_data.get('data', []))} anotadores")
            
            # Exportar no formato solicitado
            if export_format == 'csv':
                return self._export_csv(report_data)
            elif export_format == 'pdf':
                return self._export_pdf(report_data)
                
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Erro de base de dados ao exportar relatório de anotadores: {str(e)}")
            return Response(
                {"detail": "Database is slow or unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            print(f"[EXPORT DEBUG] ERRO ao exportar relatório:")
            print(f"[EXPORT DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[EXPORT DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[EXPORT DEBUG] Traceback completo:")
            traceback.print_exc()
            
            logger.error(f"Erro inesperado ao exportar relatório de anotadores: {str(e)}")
            return Response(
                {"detail": "Erro interno do servidor. Tente novamente mais tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_query_params(self, query_params):
        """Processar parâmetros da query string (mesmo método da view principal)"""
        processed = {}
        
        # Processar project_ids (obrigatório)
        if 'project_ids' in query_params:
            try:
                processed['project_ids'] = [
                    int(x.strip()) for x in query_params['project_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['project_ids'] = []
        
        # Processar user_ids (opcional)
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                processed['user_ids'] = [
                    int(x.strip()) for x in query_params['user_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['user_ids'] = []
        
        # Processar label_ids (opcional)
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                processed['label_ids'] = [
                    int(x.strip()) for x in query_params['label_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['label_ids'] = []
        
        # Processar perspective_ids (opcional)
        if 'perspective_ids' in query_params and query_params['perspective_ids']:
            try:
                processed['perspective_ids'] = [
                    int(x.strip()) for x in query_params['perspective_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_ids'] = []
        
        # Processar dataset_names (opcional)
        if 'dataset_names' in query_params and query_params['dataset_names']:
            processed['dataset_names'] = [
                x.strip() for x in query_params['dataset_names'].split(',') if x.strip()
            ]
        
        # Processar datas (opcional)
        if 'date_from' in query_params and query_params['date_from']:
            processed['date_from'] = query_params['date_from']
        
        if 'date_to' in query_params and query_params['date_to']:
            processed['date_to'] = query_params['date_to']
        
        # Processar perspective_question_ids (opcional)
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                processed['perspective_question_ids'] = [
                    int(x.strip()) for x in query_params['perspective_question_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_question_ids'] = []
        
        # Processar perspective_answer_ids (opcional)
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                processed['perspective_answer_ids'] = [
                    int(x.strip()) for x in query_params['perspective_answer_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_answer_ids'] = []
        
        return processed

    def _check_project_permissions(self, user, project_ids):
        """Verificar se o utilizador tem permissão para aceder aos projetos (mesmo método da view principal)"""
        from projects.models import Project, Member
        from roles.models import Role
        from django.conf import settings
        
        # Se for superuser, tem acesso a tudo
        if user.is_superuser:
            return True
        
        # Verificar se é admin ou staff de todos os projetos
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                member = Member.objects.get(project=project, user=user)
                
                # Verificar se tem role de admin ou annotation approver
                admin_role = Role.objects.get(name=settings.ROLE_PROJECT_ADMIN)
                approver_role = Role.objects.get(name=settings.ROLE_ANNOTATION_APPROVER)
                
                if member.role not in [admin_role, approver_role]:
                    return False
                    
            except (Project.DoesNotExist, Member.DoesNotExist, Role.DoesNotExist):
                return False
        
        return True

    def _export_csv(self, report_data):
        """Exportar relatório em formato CSV melhorado"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="annotators_report.csv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Cabeçalho do relatório
        writer.writerow(['=== ANNOTATORS REPORT ==='])
        writer.writerow([])
        
        # Obter informações do projeto
        project_name = "N/A"
        if report_data.get('data') and len(report_data['data']) > 0:
            first_item = report_data['data'][0]
            project_name = first_item.get('project_name', "N/A")
        
        # Informações do projeto
        writer.writerow(['Project:', project_name])
        writer.writerow(['Generation Date:', timezone.now().strftime('%d/%m/%Y %H:%M:%S')])
        writer.writerow([])
        
        # Estatísticas resumo
        data_items = report_data.get('data', [])
        total_annotators = len(data_items)
        total_annotations = sum(sum(item.get('label_breakdown', {}).values()) for item in data_items)
        
        # Calcular labels únicas
        unique_labels = set()
        for item in data_items:
            label_breakdown = item.get('label_breakdown', {})
            if label_breakdown:
                unique_labels.update(label_breakdown.keys())
        
        writer.writerow(['=== SUMMARY STATISTICS ==='])
        writer.writerow(['Total Annotators:', total_annotators])
        writer.writerow(['Total Annotations:', total_annotations])
        writer.writerow(['Different Labels:', len(unique_labels)])
        writer.writerow([])
        
        # Informações sobre filtros aplicados
        writer.writerow(['=== APPLIED FILTERS ==='])
        query_params = getattr(self.request, 'query_params', self.request.GET)
        
        # Usuários
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                from django.contrib.auth.models import User
                user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                users = User.objects.filter(id__in=user_ids)
                user_names = [user.username for user in users]
                writer.writerow(['Users:', ', '.join(user_names)])
            except Exception:
                writer.writerow(['Users:', query_params['user_ids']])
        
        # Labels
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                from label_types.models import CategoryType, SpanType, RelationType
                label_ids = [int(lid.strip()) for lid in query_params['label_ids'].split(',') if lid.strip()]
                
                label_names = []
                label_names.extend([label.text for label in CategoryType.objects.filter(id__in=label_ids)])
                label_names.extend([label.text for label in SpanType.objects.filter(id__in=label_ids)])
                label_names.extend([label.text for label in RelationType.objects.filter(id__in=label_ids)])
                
                writer.writerow(['Labels:', ', '.join(label_names)])
            except Exception:
                writer.writerow(['Labels:', query_params['label_ids']])
        
        # Datasets
        if 'dataset_names' in query_params and query_params['dataset_names']:
            datasets = [name.strip() for name in query_params['dataset_names'].split(',') if name.strip()]
            writer.writerow(['Datasets:', ', '.join(datasets)])
        
        # Perguntas da perspectiva
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                from projects.models import Question
                question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                questions = Question.objects.filter(id__in=question_ids)
                question_texts = [q.question for q in questions]
                writer.writerow(['Perspective Questions:', ', '.join(question_texts)])
            except Exception:
                writer.writerow(['Perspective Questions:', query_params['perspective_question_ids']])
        
        # Respostas da perspectiva
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                from projects.models import Answer
                answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                answers = Answer.objects.filter(id__in=answer_ids)
                answer_texts = [a.answer_text or a.answer_option or f"Answer {a.id}" for a in answers]
                writer.writerow(['Perspective Answers:', ', '.join(answer_texts)])
            except Exception:
                writer.writerow(['Perspective Answers:', query_params['perspective_answer_ids']])
        
        # Datas
        if 'date_from' in query_params and query_params['date_from']:
            writer.writerow(['Start Date:', query_params['date_from']])
        if 'date_to' in query_params and query_params['date_to']:
            writer.writerow(['End Date:', query_params['date_to']])
        
        writer.writerow([])
        
        # Dados detalhados organizados por linhas (formato vertical)
        writer.writerow(['=== DETAILED DATA (ORGANIZED FORMAT) ==='])
        writer.writerow([])
        
        # Dados dos anotadores - formato vertical para melhor legibilidade
        for i, item in enumerate(data_items, 1):
            # Separador entre anotadores
            writer.writerow([f'--- ANNOTATOR {i} ---'])
            
            # Informações básicas
            writer.writerow(['Username:', item.get('annotator_username', 'N/A')])
            writer.writerow(['Full Name:', item.get('annotator_name', 'N/A')])
            writer.writerow([])
            
            # Labels utilizadas
            writer.writerow(['LABELS USED:'])
            label_breakdown = item.get('label_breakdown', {})
            if label_breakdown:
                for label, count in label_breakdown.items():
                    writer.writerow(['', f'{label}', f'{count} annotations'])
            else:
                writer.writerow(['', 'No labels used'])
            writer.writerow([])
            
            # Datasets e suas labels
            writer.writerow(['DATASETS AND LABELS:'])
            dataset_breakdown = item.get('dataset_label_breakdown', {})
            if dataset_breakdown:
                for dataset, labels in dataset_breakdown.items():
                    writer.writerow(['', f'Dataset: {dataset}'])
                    if labels:
                        for label, count in labels.items():
                            writer.writerow(['', '', f'{label}: {count} annotations'])
                        dataset_total = sum(labels.values())
                        writer.writerow(['', '', f'Total in dataset: {dataset_total}'])
                    else:
                        writer.writerow(['', '', 'No annotations in this dataset'])
                    writer.writerow([''])
            else:
                writer.writerow(['', 'No datasets found'])
            writer.writerow([])
            
            # Perguntas e respostas da perspectiva
            writer.writerow(['PERSPECTIVE QUESTIONS AND ANSWERS:'])
            qa_data = item.get('perspective_questions_answers', {})
            if qa_data:
                if qa_data.get('questions') and qa_data.get('answers'):
                    # Criar mapa de perguntas
                    questions_map = {q['question_id']: q['question_text'] for q in qa_data['questions']}
                    
                    # Agrupar respostas por pergunta
                    answers_by_question = {}
                    for answer in qa_data['answers']:
                        question_id = answer['question_id']
                        if question_id not in answers_by_question:
                            answers_by_question[question_id] = []
                        answers_by_question[question_id].append(answer['answer_text'])
                    
                    # Mostrar cada pergunta e suas respostas
                    for question_id, answers in answers_by_question.items():
                        question_text = questions_map.get(question_id, f"Question {question_id}")
                        writer.writerow(['', f'Question: {question_text}'])
                        for answer in answers:
                            writer.writerow(['', '', f'Answer: {answer}'])
                        writer.writerow([''])
                else:
                    writer.writerow(['', 'No questions/answers found'])
            else:
                writer.writerow(['', 'No perspective questions/answers'])
            
            # Linha separadora entre anotadores
            writer.writerow([])
            writer.writerow(['=' * 50])
            writer.writerow([])
        
        return response

    def _export_pdf(self, report_data):
        """Exportar relatório em formato PDF melhorado com design profissional"""
        try:
            import io
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
            from reportlab.lib.units import inch, cm
            from datetime import datetime

            print(f"[PDF DEBUG] Iniciando exportação PDF com {len(report_data.get('data', []))} itens")

            # Configurar buffer para o PDF
            buffer = io.BytesIO()
            
            # Configurar documento PDF (A4 landscape para mais espaço)
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Configurar estilos
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            styles.add(ParagraphStyle(
                name='MainTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor('#1976d2'),
                fontName='Helvetica-Bold'
            ))
            
            styles.add(ParagraphStyle(
                name='SectionTitle',
                parent=styles['Heading2'],
                fontSize=14,
                alignment=TA_LEFT,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.HexColor('#424242'),
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=colors.HexColor('#e0e0e0'),
                borderPadding=5,
                backColor=colors.HexColor('#f5f5f5')
            ))
            
            styles.add(ParagraphStyle(
                name='InfoText',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_LEFT,
                spaceAfter=4,
                textColor=colors.HexColor('#666666')
            ))
            
            styles.add(ParagraphStyle(
                name='StatText',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=6,
                textColor=colors.HexColor('#1976d2'),
                fontName='Helvetica-Bold'
            ))
            
            styles.add(ParagraphStyle(
                name='TableHeader',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.white,
                fontName='Helvetica-Bold'
            ))
            
            styles.add(ParagraphStyle(
                name='TableCell',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_LEFT,
                textColor=colors.HexColor('#424242')
            ))
            
            # Elementos do documento
            elements = []
            
            # Cabeçalho principal
            elements.append(Paragraph("ANNOTATORS REPORT", styles['MainTitle']))
            elements.append(Spacer(1, 10))
            
            # Obter informações do projeto
            project_name = "N/A"
            if report_data.get('data') and len(report_data['data']) > 0:
                first_item = report_data['data'][0]
                project_name = first_item.get('project_name', "N/A")
            
            # Informações do projeto em tabela
            project_info = [
                ['Projeto:', project_name],
                ['Data de Geração:', timezone.now().strftime('%d/%m/%Y às %H:%M:%S')]
            ]
            
            project_table = Table(project_info, colWidths=[4*cm, 11*cm])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbbbbb')),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(project_table)
            elements.append(Spacer(1, 20))
            
            # Estatísticas resumo
            data_items = report_data.get('data', [])
            total_annotators = len(data_items)
            total_annotations = sum(sum(item.get('label_breakdown', {}).values()) for item in data_items)
            
            # Calcular labels únicas
            unique_labels = set()
            for item in data_items:
                label_breakdown = item.get('label_breakdown', {})
                if label_breakdown:
                    unique_labels.update(label_breakdown.keys())
            
            elements.append(Paragraph("ESTATÍSTICAS RESUMO", styles['SectionTitle']))
            
            # Criar tabela de estatísticas em formato de cards
            stats_data = [
                ['Total de Anotadores', 'Total de Anotações', 'Labels Diferentes'],
                [str(total_annotators), str(total_annotations), str(len(unique_labels))]
            ]
            
            stats_table = Table(stats_data, colWidths=[5*cm, 5*cm, 5*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e3f2fd')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 14),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#1976d2')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1976d2')),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(KeepTogether([stats_table]))
            elements.append(Spacer(1, 20))
            
            # Filtros aplicados
            elements.append(Paragraph("FILTROS APLICADOS", styles['SectionTitle']))
            
            query_params = getattr(self.request, 'query_params', self.request.GET)
            filter_info = []
            
            # Usuários
            if 'user_ids' in query_params and query_params['user_ids']:
                try:
                    from django.contrib.auth.models import User
                    user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                    users = User.objects.filter(id__in=user_ids)
                    user_names = [user.username for user in users]
                    filter_info.append(['Utilizadores:', ', '.join(user_names)])
                except Exception:
                    filter_info.append(['Utilizadores:', query_params['user_ids']])
            
            # Labels
            if 'label_ids' in query_params and query_params['label_ids']:
                try:
                    from label_types.models import CategoryType, SpanType, RelationType
                    label_ids = [int(lid.strip()) for lid in query_params['label_ids'].split(',') if lid.strip()]
                    
                    label_names = []
                    label_names.extend([label.text for label in CategoryType.objects.filter(id__in=label_ids)])
                    label_names.extend([label.text for label in SpanType.objects.filter(id__in=label_ids)])
                    label_names.extend([label.text for label in RelationType.objects.filter(id__in=label_ids)])
                    
                    filter_info.append(['Labels:', ', '.join(label_names)])
                except Exception:
                    filter_info.append(['Labels:', query_params['label_ids']])
            
            # Datasets
            if 'dataset_names' in query_params and query_params['dataset_names']:
                datasets = [name.strip() for name in query_params['dataset_names'].split(',') if name.strip()]
                filter_info.append(['Datasets:', ', '.join(datasets)])
            
            # Perguntas da perspectiva
            if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
                try:
                    from projects.models import Question
                    question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                    questions = Question.objects.filter(id__in=question_ids)
                    question_texts = [q.question for q in questions]
                    filter_info.append(['Perguntas da Perspectiva:', ', '.join(question_texts)])
                except Exception:
                    filter_info.append(['Perguntas da Perspectiva:', query_params['perspective_question_ids']])
            
            # Respostas da perspectiva
            if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
                try:
                    from projects.models import Answer
                    answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                    answers = Answer.objects.filter(id__in=answer_ids)
                    answer_texts = [a.answer_text or a.answer_option or f"Resposta {a.id}" for a in answers]
                    filter_info.append(['Respostas da Perspectiva:', ', '.join(answer_texts)])
                except Exception:
                    filter_info.append(['Respostas da Perspectiva:', query_params['perspective_answer_ids']])
            
            # Datas
            if 'date_from' in query_params and query_params['date_from']:
                filter_info.append(['Data Início:', query_params['date_from']])
            if 'date_to' in query_params and query_params['date_to']:
                filter_info.append(['Data Fim:', query_params['date_to']])
            
            if filter_info:
                filter_table = Table(filter_info, colWidths=[4*cm, 11*cm])
                filter_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(KeepTogether([filter_table]))
            else:
                elements.append(Paragraph("Nenhum filtro específico aplicado", styles['InfoText']))
            
            elements.append(Spacer(1, 20))
            
            # Dados detalhados
            detailed_title = Paragraph("DADOS DETALHADOS", styles['SectionTitle'])
            
            if data_items:
                # Cabeçalho da tabela
                table_data = [
                    [
                        Paragraph('Utilizador', styles['TableHeader']),
                        Paragraph('Nome', styles['TableHeader']),
                        Paragraph('Labels', styles['TableHeader']),
                        Paragraph('Datasets', styles['TableHeader']),
                        Paragraph('Perguntas/Respostas', styles['TableHeader'])
                    ]
                ]
                
                # Dados dos anotadores
                for i, item in enumerate(data_items):
                    # Formatar labels
                    label_breakdown = []
                    label_data = item.get('label_breakdown', {})
                    if label_data:
                        for label, count in label_data.items():
                            label_breakdown.append(f"{label}: {count}")
                    label_text = '<br/>'.join(label_breakdown) if label_breakdown else 'Nenhuma'
                    
                    # Formatar datasets
                    dataset_breakdown = []
                    dataset_data = item.get('dataset_label_breakdown', {})
                    if dataset_data:
                        for dataset, labels in dataset_data.items():
                            dataset_labels = []
                            for label, count in labels.items():
                                dataset_labels.append(f"{label}: {count}")
                            dataset_breakdown.append(f"<b>{dataset}</b><br/>({'; '.join(dataset_labels)})")
                    dataset_text = '<br/><br/>'.join(dataset_breakdown) if dataset_breakdown else 'Nenhum'
                    
                    # Formatar perguntas e respostas
                    qa_breakdown = []
                    qa_data = item.get('perspective_questions_answers', {})
                    if qa_data:
                        if qa_data.get('questions') and qa_data.get('answers'):
                            questions_map = {q['question_id']: q['question_text'] for q in qa_data['questions']}
                            
                            answers_by_question = {}
                            for answer in qa_data['answers']:
                                question_id = answer['question_id']
                                if question_id not in answers_by_question:
                                    answers_by_question[question_id] = []
                                answers_by_question[question_id].append(answer['answer_text'])
                            
                            for question_id, answers in answers_by_question.items():
                                question_text = questions_map.get(question_id, f"Pergunta {question_id}")
                                qa_breakdown.append(f"<b>{question_text}</b><br/>{', '.join(answers)}")
                    
                    qa_text = '<br/><br/>'.join(qa_breakdown) if qa_breakdown else 'Nenhuma'
                    
                    # Cor alternada para as linhas
                    row_color = colors.HexColor('#f9f9f9') if i % 2 == 0 else colors.white
                    
                    table_data.append([
                        Paragraph(item.get('annotator_username', 'N/A'), styles['TableCell']),
                        Paragraph(item.get('annotator_name', 'N/A'), styles['TableCell']),
                        Paragraph(label_text, styles['TableCell']),
                        Paragraph(dataset_text, styles['TableCell']),
                        Paragraph(qa_text, styles['TableCell'])
                    ])
                
                # Criar tabela
                main_table = Table(table_data, colWidths=[3.5*cm, 3.5*cm, 5.5*cm, 5.5*cm, 6*cm])
                main_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    
                    # Dados
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    
                    # Bordas e padding
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    
                    # Cores alternadas
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ]))
                
                # Adicionar título e tabela juntos com KeepTogether
                elements.append(KeepTogether([detailed_title, Spacer(1, 10), main_table]))
            else:
                no_data_msg = Paragraph("Nenhum dado encontrado para os filtros aplicados.", styles['InfoText'])
                elements.append(KeepTogether([detailed_title, Spacer(1, 10), no_data_msg]))
            
            # Construir PDF
            doc.build(elements)
            
            # Preparar resposta
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="relatorio_anotadores.pdf"'
            
            print(f"[PDF DEBUG] PDF gerado com sucesso")
            return response
            
        except Exception as e:
            print(f"[PDF DEBUG] ERRO na exportação PDF: {e}")
            import traceback
            traceback.print_exc()
            
            # Retornar erro HTTP 500 com detalhes
            from django.http import JsonResponse
            return JsonResponse({
                'error': f'Erro ao gerar PDF: {str(e)}'
            }, status=500)


# Novas views para relatório de anotações

class AnnotationReportView(APIView):
    """
    View para gerar relatório sobre anotações com vários filtros
    """
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    @swagger_auto_schema(
        operation_description="Gerar relatório sobre anotações com filtros",
        query_serializer=AnnotationReportFilterSerializer,
        responses={
            200: AnnotationReportResponseSerializer,
            400: "Parâmetros inválidos",
            403: "Sem permissão para aceder aos projetos especificados"
        },
        manual_parameters=[
            openapi.Parameter(
                'project_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos projetos (separados por vírgula)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'user_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos utilizadores (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'example_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos exemplos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Data de início (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Data de fim (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'label_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos rótulos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'annotation_types',
                openapi.IN_QUERY,
                description="Lista de tipos de anotação (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Página dos resultados",
                type=openapi.TYPE_INTEGER,
                default=1,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Tamanho da página",
                type=openapi.TYPE_INTEGER,
                default=50,
                required=False
            ),
            openapi.Parameter(
                'discrepancy_filter',
                openapi.IN_QUERY,
                description="Filtro de discrepâncias: all, with_discrepancy, without_discrepancy",
                type=openapi.TYPE_STRING,
                enum=['all', 'with_discrepancy', 'without_discrepancy'],
                required=False
            ),
            openapi.Parameter(
                'perspective_question_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perguntas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_answer_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das respostas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Gerar relatório sobre anotações"""
        
        # Processar parâmetros da query string
        query_params_source = getattr(request, 'query_params', request.GET)
        query_params = self._process_query_params(query_params_source)
        
        # Validar parâmetros
        serializer = AnnotationReportFilterSerializer(data=query_params)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # Verificar permissões para os projetos especificados
        project_ids = validated_data['project_ids']
        if not self._check_project_permissions(request.user, project_ids):
            return Response(
                {"detail": "Não tem permissão para aceder a alguns dos projetos especificados"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Obter página e tamanho da página
            page = int(query_params_source.get('page', 1))
            page_size = int(query_params_source.get('page_size', 50))
            
            # Limitar tamanho da página
            if page_size > 100:
                page_size = 100
                
            # Gerar relatório
            report_data = AnnotationReportService.get_report(
                **validated_data,
                page=page,
                page_size=page_size
            )
            
            return Response(report_data, status=status.HTTP_200_OK)
            
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Erro de base de dados ao gerar relatório de anotações: {str(e)}")
            return Response(
                {"detail": "Database is slow or unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao gerar relatório de anotações: {str(e)}")
            return Response(
                {"detail": "Erro interno do servidor. Tente novamente mais tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_query_params(self, query_params):
        """Processar parâmetros da query string"""
        processed = {}
        
        # Processar project_ids (obrigatório)
        if 'project_ids' in query_params:
            try:
                processed['project_ids'] = [
                    int(x.strip()) for x in query_params['project_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['project_ids'] = []
        
        # Processar user_ids (opcional)
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                processed['user_ids'] = [
                    int(x.strip()) for x in query_params['user_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['user_ids'] = []
        
        # Processar example_ids (opcional)
        if 'example_ids' in query_params and query_params['example_ids']:
            try:
                processed['example_ids'] = [
                    int(x.strip()) for x in query_params['example_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['example_ids'] = []
        
        # Processar label_ids (opcional)
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                processed['label_ids'] = [
                    int(x.strip()) for x in query_params['label_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['label_ids'] = []
        
        # Processar annotation_types (opcional)
        if 'annotation_types' in query_params and query_params['annotation_types']:
            processed['annotation_types'] = [
                x.strip() for x in query_params['annotation_types'].split(',') if x.strip()
            ]
        
        # Processar perspective_question_ids (opcional)
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                processed['perspective_question_ids'] = [
                    int(x.strip()) for x in query_params['perspective_question_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_question_ids'] = []
        
        # Processar perspective_answer_ids (opcional)
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                processed['perspective_answer_ids'] = [
                    int(x.strip()) for x in query_params['perspective_answer_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_answer_ids'] = []
        
        # Processar datas (opcional)
        if 'date_from' in query_params and query_params['date_from']:
            processed['date_from'] = query_params['date_from']
        
        if 'date_to' in query_params and query_params['date_to']:
            processed['date_to'] = query_params['date_to']
        
        # Processar filtro de discrepâncias (opcional)
        if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
            processed['discrepancy_filter'] = query_params['discrepancy_filter']
        
        return processed

    def _check_project_permissions(self, user, project_ids):
        """Verificar se o utilizador tem permissão para aceder aos projetos"""
        from projects.models import Project, Member
        from roles.models import Role
        from django.conf import settings
        
        # Se for superuser, tem acesso a tudo
        if user.is_superuser:
            return True
        
        # Verificar se é admin ou staff de todos os projetos
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                member = Member.objects.get(project=project, user=user)
                
                # Verificar se tem role de admin ou annotation approver
                admin_role = Role.objects.get(name=settings.ROLE_PROJECT_ADMIN)
                approver_role = Role.objects.get(name=settings.ROLE_ANNOTATION_APPROVER)
                
                if member.role not in [admin_role, approver_role]:
                    return False
                    
            except (Project.DoesNotExist, Member.DoesNotExist, Role.DoesNotExist):
                return False
        
        return True


class AnnotationReportExportView(APIView):
    """
    View para exportar relatório sobre anotações em múltiplos formatos
    """
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    
    @swagger_auto_schema(
        operation_description="Exportar relatório sobre anotações em CSV ou PDF",
        query_serializer=AnnotationReportFilterSerializer,
        manual_parameters=[
            openapi.Parameter(
                'export_format',
                openapi.IN_QUERY,
                description="Formato de exportação: csv ou pdf",
                type=openapi.TYPE_STRING,
                enum=['csv', 'pdf'],
                default='csv',
                required=False
            ),
            openapi.Parameter(
                'project_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos projetos (separados por vírgula)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'user_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos utilizadores (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'example_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos exemplos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Data de início (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Data de fim (formato ISO, opcional)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'label_ids',
                openapi.IN_QUERY,
                description="Lista de IDs dos rótulos (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'annotation_types',
                openapi.IN_QUERY,
                description="Lista de tipos de anotação (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'max_results',
                openapi.IN_QUERY,
                description="Número máximo de resultados (até 1000000)",
                type=openapi.TYPE_INTEGER,
                default=1000,
                required=False
            ),
            openapi.Parameter(
                'discrepancy_filter',
                openapi.IN_QUERY,
                description="Filtro de discrepâncias: all, with_discrepancy, without_discrepancy",
                type=openapi.TYPE_STRING,
                enum=['all', 'with_discrepancy', 'without_discrepancy'],
                required=False
            ),
            openapi.Parameter(
                'perspective_question_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das perguntas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'perspective_answer_ids',
                openapi.IN_QUERY,
                description="Lista de IDs das respostas da perspectiva (separados por vírgula, opcional)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: "Arquivo exportado",
            400: "Parâmetros inválidos",
            403: "Sem permissão para aceder aos projetos especificados"
        }
    )
    def get(self, request, *args, **kwargs):
        """Exportar relatório sobre anotações"""
        
        # Usar request.GET para compatibilidade com Django padrão e DRF
        query_params_source = getattr(request, 'query_params', request.GET)
        
        # Obter formato de exportação (suportar tanto 'format' quanto 'export_format' para compatibilidade)
        export_format = query_params_source.get('export_format', query_params_source.get('format', 'csv')).lower()
        
        if export_format not in ['csv', 'pdf']:
            return Response(
                {"detail": "Formato inválido. Use: csv ou pdf"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Processar parâmetros da query string (reutilizar lógica da view principal)
        query_params = self._process_query_params(query_params_source)
        
        # Validar parâmetros
        serializer = AnnotationReportFilterSerializer(data=query_params)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # Verificar permissões para os projetos especificados
        project_ids = validated_data['project_ids']
        if not self._check_project_permissions(request.user, project_ids):
            return Response(
                {"detail": "Não tem permissão para aceder a alguns dos projetos especificados"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Obter limite máximo de resultados (com limite para evitar excesso)
            max_results = min(1000000, int(query_params_source.get('max_results', 1000)))
            
            # Gerar relatório (forçar page=1 e max_results como page_size)
            report_data = AnnotationReportService.get_report(
                **validated_data,
                page=1,
                page_size=max_results
            )
            
            # Exportar no formato solicitado
            if export_format == 'csv':
                return self._export_csv(report_data)
            elif export_format == 'pdf':
                return self._export_pdf(report_data)
                
        except (DatabaseError, OperationalError) as e:
            logger.error(f"Erro de base de dados ao exportar relatório de anotações: {str(e)}")
            return Response(
                {"detail": "Database is slow or unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            print(f"[EXPORT DEBUG] ERRO ao exportar relatório:")
            print(f"[EXPORT DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[EXPORT DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[EXPORT DEBUG] Traceback completo:")
            traceback.print_exc()
            
            logger.error(f"Erro inesperado ao exportar relatório de anotações: {str(e)}")
            return Response(
                {"detail": "Erro interno do servidor. Tente novamente mais tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_query_params(self, query_params):
        """Processar parâmetros da query string"""
        processed = {}
        
        # Processar project_ids (obrigatório)
        if 'project_ids' in query_params:
            try:
                processed['project_ids'] = [
                    int(x.strip()) for x in query_params['project_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['project_ids'] = []
        
        # Processar user_ids (opcional)
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                processed['user_ids'] = [
                    int(x.strip()) for x in query_params['user_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['user_ids'] = []
        
        # Processar example_ids (opcional)
        if 'example_ids' in query_params and query_params['example_ids']:
            try:
                processed['example_ids'] = [
                    int(x.strip()) for x in query_params['example_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['example_ids'] = []
        
        # Processar label_ids (opcional)
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                processed['label_ids'] = [
                    int(x.strip()) for x in query_params['label_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['label_ids'] = []
        
        # Processar annotation_types (opcional)
        if 'annotation_types' in query_params and query_params['annotation_types']:
            processed['annotation_types'] = [
                x.strip() for x in query_params['annotation_types'].split(',') if x.strip()
            ]
        
        # Processar perspective_question_ids (opcional)
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                processed['perspective_question_ids'] = [
                    int(x.strip()) for x in query_params['perspective_question_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_question_ids'] = []
        
        # Processar perspective_answer_ids (opcional)
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                processed['perspective_answer_ids'] = [
                    int(x.strip()) for x in query_params['perspective_answer_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['perspective_answer_ids'] = []
        
        # Processar datas (opcional)
        if 'date_from' in query_params and query_params['date_from']:
            processed['date_from'] = query_params['date_from']
        
        if 'date_to' in query_params and query_params['date_to']:
            processed['date_to'] = query_params['date_to']
        
        # Processar filtro de discrepâncias (opcional)
        if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
            processed['discrepancy_filter'] = query_params['discrepancy_filter']
        
        return processed

    def _check_project_permissions(self, user, project_ids):
        """Verificar permissões como na view principal"""
        from projects.models import Project, Member
        from roles.models import Role
        from django.conf import settings
        
        if user.is_superuser:
            return True
        
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                member = Member.objects.get(project=project, user=user)
                
                admin_role = Role.objects.get(name=settings.ROLE_PROJECT_ADMIN)
                approver_role = Role.objects.get(name=settings.ROLE_ANNOTATION_APPROVER)
                
                if member.role not in [admin_role, approver_role]:
                    return False
                    
            except (Project.DoesNotExist, Member.DoesNotExist, Role.DoesNotExist):
                return False
        
        return True

    def _export_csv(self, report_data):
        """Exportar relatório em formato CSV melhorado"""
        from django.utils import timezone
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="annotations_report.csv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Obter informações do projeto (assumindo que todas as anotações são do mesmo projeto)
        project_name = "N/A"
        project_id = ""
        if report_data.get('data') and len(report_data['data']) > 0:
            first_item = report_data['data'][0]
            project_name = first_item.get('project_name', "N/A")
            project_id = first_item.get('project_id', "")
        
        # Adicionar cabeçalho com informações do projeto
        writer.writerow(['=== ANNOTATIONS REPORT ==='])
        writer.writerow(['Generated on:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Project Name:', project_name])
        if project_id:
            writer.writerow(['Project ID:', project_id])
        writer.writerow([])
        
        # Recuperar os filtros da query string original
        query_params = getattr(self, 'request', None)
        if query_params:
            query_params = getattr(query_params, 'query_params', getattr(query_params, 'GET', {}))
        else:
            query_params = {}
        
        # Verificar se há filtros aplicados
        has_filters = any([
            query_params.get('user_ids'),
            query_params.get('label_ids'),
            query_params.get('example_ids'),
            query_params.get('discrepancy_filter'),
            query_params.get('perspective_question_ids'),
            query_params.get('perspective_answer_ids'),
            query_params.get('date_from'),
            query_params.get('date_to')
        ])
        
        # Adicionar informações sobre os filtros utilizados
        writer.writerow(['=== APPLIED FILTERS ==='])
        
        if not has_filters:
            writer.writerow(['No specific filters applied - showing all annotations'])
        
        # Usuários - converter IDs para nomes
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                from django.contrib.auth.models import User
                user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                users = User.objects.filter(id__in=user_ids)
                user_names = [user.username for user in users]
                writer.writerow(['Users:', ', '.join(user_names)])
            except Exception:
                writer.writerow(['Users:', query_params['user_ids']])
        
        # Labels - converter IDs para nomes
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                from label_types.models import CategoryType, SpanType, RelationType
                label_ids = [int(lid.strip()) for lid in query_params['label_ids'].split(',') if lid.strip()]
                
                # Buscar em todos os tipos de label
                category_labels = CategoryType.objects.filter(id__in=label_ids)
                span_labels = SpanType.objects.filter(id__in=label_ids)
                relation_labels = RelationType.objects.filter(id__in=label_ids)
                
                label_names = []
                label_names.extend([label.text for label in category_labels])
                label_names.extend([label.text for label in span_labels])
                label_names.extend([label.text for label in relation_labels])
                
                writer.writerow(['Labels:', ', '.join(label_names)])
            except Exception:
                writer.writerow(['Labels:', query_params['label_ids']])
        
        # Exemplos - converter IDs para nomes
        if 'example_ids' in query_params and query_params['example_ids']:
            try:
                from examples.models import Example
                example_ids = [int(eid.strip()) for eid in query_params['example_ids'].split(',') if eid.strip()]
                examples = Example.objects.filter(id__in=example_ids)
                
                example_names = []
                for example in examples:
                    if hasattr(example, 'upload_name') and example.upload_name:
                        example_names.append(str(example.upload_name))
                    elif hasattr(example, 'filename') and example.filename:
                        example_names.append(str(example.filename))
                    elif hasattr(example, 'text') and example.text:
                        text = str(example.text)
                        example_names.append(text[:50] + ('...' if len(text) > 50 else ''))
                    else:
                        example_names.append(f"Example {example.id}")
                
                writer.writerow(['Examples:', ', '.join(example_names)])
            except Exception:
                writer.writerow(['Examples:', query_params['example_ids']])
        
        # Filtro de discrepâncias
        if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
            discrepancy_text = {
                'all': 'All annotations',
                'with_discrepancy': 'Only annotations with discrepancies',
                'without_discrepancy': 'Only annotations without discrepancies'
            }.get(query_params['discrepancy_filter'], query_params['discrepancy_filter'])
            writer.writerow(['Discrepancy Filter:', discrepancy_text])
        
        # Perguntas da perspectiva
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                from projects.models import Question
                question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                questions = Question.objects.filter(id__in=question_ids)
                question_texts = [q.question for q in questions]
                writer.writerow(['Perspective Questions:', ', '.join(question_texts)])
            except Exception:
                writer.writerow(['Perspective Questions:', query_params['perspective_question_ids']])
        
        # Respostas da perspectiva
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                from projects.models import Answer
                answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                answers = Answer.objects.filter(id__in=answer_ids)
                answer_texts = [a.answer_text or a.answer_option or f"Answer {a.id}" for a in answers]
                writer.writerow(['Perspective Answers:', ', '.join(answer_texts)])
            except Exception:
                writer.writerow(['Perspective Answers:', query_params['perspective_answer_ids']])
        
        # Datas
        if 'date_from' in query_params and query_params['date_from']:
            writer.writerow(['Start Date:', query_params['date_from']])
        if 'date_to' in query_params and query_params['date_to']:
            writer.writerow(['End Date:', query_params['date_to']])
        
        # Estatísticas do relatório
        writer.writerow([])  # Linha em branco
        writer.writerow(['=== REPORT STATISTICS ==='])
        
        # Calcular estatísticas
        total_annotations = len(report_data.get('data', []))
        unique_users = set()
        unique_examples = set()
        unique_labels = set()
        
        for item in report_data.get('data', []):
            if item.get('username'):
                unique_users.add(item['username'])
            if item.get('example_name'):
                unique_examples.add(item['example_name'])
            if item.get('label_text'):
                unique_labels.add(item['label_text'])
        
        writer.writerow(['Total Annotations:', total_annotations])
        writer.writerow(['Unique Users:', len(unique_users)])
        writer.writerow(['Unique Examples:', len(unique_examples)])
        writer.writerow(['Unique Labels:', len(unique_labels)])
        
        writer.writerow([])  # Linha em branco
        writer.writerow(['=== ANNOTATION DATA ==='])
        
        # Cabeçalho da tabela
        writer.writerow([
            'Example',
            'User',
            'Label',
            'Creation Date',
            'Details'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar detalhes como string JSON simplificada
            detail_str = ""
            detail_data = item.get('detail', {})
            if detail_data and isinstance(detail_data, dict):
                detail_str = "; ".join([f"{k}: {v}" for k, v in detail_data.items()])
            
            # Formatar data (agora é uma string ISO)
            date_str = '-'
            created_at = item.get('created_at')
            if created_at:
                # Se já for string, usar diretamente ou formatar
                try:
                    from datetime import datetime
                    # Tentar converter para datetime e formatar
                    dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, AttributeError, TypeError):
                    # Se falhar, usar a string original
                    date_str = str(created_at)
            
            writer.writerow([
                item.get('example_name', '-'),
                item.get('username', '-'),
                item.get('label_text', '-') or '-',
                date_str,
                detail_str
            ])
        
        return response



    def _export_pdf(self, report_data):
        """Exportar relatório em formato PDF"""
        try:
            import io
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.lib.units import inch, cm

            print(f"[PDF DEBUG] Iniciando exportação PDF com {len(report_data.get('data', []))} itens")

            # Configurar buffer para o PDF
            buffer = io.BytesIO()
            
            # Configurar documento PDF (A4 landscape para mais espaço)
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20
            )
            
            # Configurar estilos
            styles = getSampleStyleSheet()
            
            # Adicionar estilo personalizado para cabeçalho
            styles.add(
                ParagraphStyle(
                    name='TitleStyle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    alignment=TA_CENTER,
                    spaceAfter=12
                )
            )
            
            # Adicionar estilo personalizado para subtítulos
            styles.add(
                ParagraphStyle(
                    name='SubtitleStyle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    alignment=TA_LEFT,
                    spaceAfter=6
                )
            )
            
            # Estilo para texto pequeno
            styles.add(
                ParagraphStyle(
                    name='SmallText',
                    parent=styles['Normal'],
                    fontSize=8,
                    alignment=TA_LEFT
                )
            )
            
            # Adicionar estilo para seções
            styles.add(
                ParagraphStyle(
                    name='SectionTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    alignment=TA_LEFT,
                    spaceAfter=8,
                    spaceBefore=12,
                    textColor=colors.HexColor('#1976d2')
                )
            )
            
            # Estilo para texto informativo
            styles.add(
                ParagraphStyle(
                    name='InfoText',
                    parent=styles['Normal'],
                    fontSize=10,
                    alignment=TA_LEFT,
                    textColor=colors.HexColor('#666666')
                )
            )
            
            # Estilo para cabeçalho de tabela
            styles.add(
                ParagraphStyle(
                    name='TableHeader',
                    parent=styles['Normal'],
                    fontSize=9,
                    alignment=TA_CENTER,
                    textColor=colors.white
                )
            )
            
            # Estilo para células de tabela
            styles.add(
                ParagraphStyle(
                    name='TableCell',
                    parent=styles['Normal'],
                    fontSize=8,
                    alignment=TA_LEFT
                )
            )
            
            # Elementos do documento
            elements = []
            
            # Título do relatório
            elements.append(Paragraph("ANNOTATIONS REPORT", styles['TitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Obter informações do projeto
            project_name = "N/A"
            if report_data.get('data') and len(report_data['data']) > 0:
                first_item = report_data['data'][0]
                project_name = first_item.get('project_name', "N/A")
            
            # Informações do projeto em tabela
            project_info = [
                ['Project:', project_name],
                ['Generation Date:', timezone.now().strftime('%d/%m/%Y at %H:%M:%S')]
            ]
            
            project_table = Table(project_info, colWidths=[4*cm, 11*cm])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbbbbb')),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(project_table)
            elements.append(Spacer(1, 20))
            
            # Adicionar informações sobre os filtros aplicados
            elements.append(Paragraph("APPLIED FILTERS", styles['SubtitleStyle']))
            
            filter_info = []
            
            # Recuperar os filtros da query string original
            query_params = getattr(self, 'request', None)
            if query_params:
                query_params = getattr(query_params, 'query_params', getattr(query_params, 'GET', {}))
            else:
                query_params = {}
            
            # Usuários - converter IDs para nomes
            if 'user_ids' in query_params and query_params['user_ids']:
                try:
                    from django.contrib.auth.models import User
                    user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                    users = User.objects.filter(id__in=user_ids)
                    user_names = [user.username for user in users]
                    filter_info.append(['Users:', ', '.join(user_names)])
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar user_ids: {e}")
                    filter_info.append(['Users:', query_params['user_ids']])
            
            # Labels - converter IDs para nomes
            if 'label_ids' in query_params and query_params['label_ids']:
                try:
                    from label_types.models import CategoryType, SpanType, RelationType
                    label_ids = [int(lid.strip()) for lid in query_params['label_ids'].split(',') if lid.strip()]
                    
                    # Buscar em todos os tipos de label
                    category_labels = CategoryType.objects.filter(id__in=label_ids)
                    span_labels = SpanType.objects.filter(id__in=label_ids)
                    relation_labels = RelationType.objects.filter(id__in=label_ids)
                    
                    label_names = []
                    label_names.extend([label.text for label in category_labels])
                    label_names.extend([label.text for label in span_labels])
                    label_names.extend([label.text for label in relation_labels])
                    
                    filter_info.append(['Labels:', ', '.join(label_names)])
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar label_ids: {e}")
                    filter_info.append(['Labels:', query_params['label_ids']])
            
            # Exemplos - converter IDs para nomes
            if 'example_ids' in query_params and query_params['example_ids']:
                try:
                    from examples.models import Example
                    example_ids = [int(eid.strip()) for eid in query_params['example_ids'].split(',') if eid.strip()]
                    examples = Example.objects.filter(id__in=example_ids)
                    
                    example_names = []
                    for example in examples:
                        if hasattr(example, 'upload_name') and example.upload_name:
                            example_names.append(str(example.upload_name))
                        elif hasattr(example, 'filename') and example.filename:
                            example_names.append(str(example.filename))
                        elif hasattr(example, 'text') and example.text:
                            text = str(example.text)
                            example_names.append(text[:30] + ('...' if len(text) > 30 else ''))
                        else:
                            example_names.append(f"Example {example.id}")
                    
                    filter_info.append(['Examples:', ', '.join(example_names)])
                except Exception:
                    filter_info.append(['Examples:', query_params['example_ids']])
            
            # Filtro de discrepâncias
            if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
                discrepancy_map = {
                    'all': 'All annotations',
                    'with_discrepancy': 'Only with discrepancies',
                    'without_discrepancy': 'Only without discrepancies'
                }
                filter_info.append(['Discrepancy Filter:', discrepancy_map.get(query_params['discrepancy_filter'], query_params['discrepancy_filter'])])
            
            # Perguntas da perspectiva
            if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
                try:
                    from projects.models import Question
                    question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                    questions = Question.objects.filter(id__in=question_ids)
                    question_texts = [q.question for q in questions]
                    filter_info.append(['Perspective Questions:', ', '.join(question_texts)])
                except Exception:
                    filter_info.append(['Perspective Questions:', query_params['perspective_question_ids']])
            
            # Respostas da perspectiva
            if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
                try:
                    from projects.models import Answer
                    answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                    answers = Answer.objects.filter(id__in=answer_ids)
                    answer_texts = [a.answer_text or a.answer_option or f"Answer {a.id}" for a in answers]
                    filter_info.append(['Perspective Answers:', ', '.join(answer_texts)])
                except Exception:
                    filter_info.append(['Perspective Answers:', query_params['perspective_answer_ids']])
            
            # Criar tabela de filtros se houver filtros
            if filter_info:
                filter_table = Table(filter_info, colWidths=[4*cm, 11*cm])
                filter_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(KeepTogether([filter_table]))
            else:
                elements.append(Paragraph("No specific filters applied", styles['Normal']))
            
            elements.append(Spacer(1, 20))
            
            # Adicionar seção de estatísticas do relatório
            elements.append(Paragraph("REPORT STATISTICS", styles['SectionTitle']))
            
            # Calcular estatísticas
            total_annotations = len(report_data.get('data', []))
            unique_users = set()
            unique_examples = set()
            unique_labels = set()
            
            for item in report_data.get('data', []):
                if item.get('username'):
                    unique_users.add(item['username'])
                if item.get('example_name'):
                    unique_examples.add(item['example_name'])
                if item.get('label_text'):
                    unique_labels.add(item['label_text'])
            
            # Criar tabela de estatísticas
            stats_info = [
                ['Total Annotations:', str(total_annotations)],
                ['Unique Users:', str(len(unique_users))],
                ['Unique Examples:', str(len(unique_examples))],
                ['Unique Labels:', str(len(unique_labels))]
            ]
            
            stats_table = Table(stats_info, colWidths=[4*cm, 3*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e8')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2e7d32')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#81c784')),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Dados detalhados
            detailed_title = Paragraph("DETAILED DATA", styles['SectionTitle'])
            
            # Obter dados das anotações
            data_items = report_data.get('data', [])
            
            if data_items:
                # Cabeçalho da tabela para anotações
                table_data = [
                    [
                        Paragraph('Example', styles['TableHeader']),
                        Paragraph('User', styles['TableHeader']),
                        Paragraph('Labels', styles['TableHeader']),
                        Paragraph('Date', styles['TableHeader'])
                    ]
                ]
                
                # Dados das anotações
                for i, item in enumerate(data_items):
                    # Formatar data
                    created_at = item.get('created_at', '')
                    if created_at:
                        try:
                            from datetime import datetime
                            if isinstance(created_at, str):
                                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                            else:
                                formatted_date = str(created_at)
                        except:
                            formatted_date = str(created_at)
                    else:
                        formatted_date = 'N/A'
                    
                    table_data.append([
                        Paragraph(item.get('example_name', 'N/A'), styles['TableCell']),
                        Paragraph(item.get('username', 'N/A'), styles['TableCell']),
                        Paragraph(item.get('label_text', 'No labels'), styles['TableCell']),
                        Paragraph(formatted_date, styles['TableCell'])
                    ])
                
                # Criar tabela
                main_table = Table(table_data, colWidths=[6*cm, 4*cm, 6*cm, 4*cm])
                main_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    
                    # Dados
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    
                    # Bordas e padding
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    
                    # Cores alternadas
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ]))
                
                # Adicionar título e tabela juntos com KeepTogether
                elements.append(KeepTogether([detailed_title, Spacer(1, 10), main_table]))
            else:
                no_data_msg = Paragraph("No data found for the applied filters.", styles['InfoText'])
                elements.append(KeepTogether([detailed_title, Spacer(1, 10), no_data_msg]))
            
            # Construir PDF
            doc.build(elements)
            
            print(f"[PDF DEBUG] PDF construído com sucesso")
            
            # Preparar resposta
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="annotations_report.pdf"'
            
            return response
            
        except Exception as e:
            print(f"[PDF DEBUG] ERRO na exportação PDF: {e}")
            import traceback
            traceback.print_exc()
            
            # Retornar erro HTTP 500 com detalhes
            from django.http import JsonResponse
            return JsonResponse({
                'error': f'Erro ao gerar PDF: {str(e)}'
            }, status=500)
