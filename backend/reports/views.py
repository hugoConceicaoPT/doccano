from django.shortcuts import render
import csv
import io
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
            
        except Exception as e:
            print(f"[DEBUG] ERRO ao gerar relatório:")
            print(f"[DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[DEBUG] Traceback completo:")
            traceback.print_exc()
            
            return Response(
                {"detail": f"Erro ao gerar relatório: {str(e)}"},
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
        operation_description="Exportar relatório sobre anotadores em CSV, PDF ou TSV",
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
        
        if export_format not in ['csv', 'pdf', 'tsv']:
            return Response(
                {"detail": "Formato inválido. Use: csv, pdf ou tsv"},
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
            elif export_format == 'tsv':
                return self._export_tsv(report_data)
            
        except Exception as e:
            print(f"[EXPORT DEBUG] ERRO ao exportar relatório:")
            print(f"[EXPORT DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[EXPORT DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[EXPORT DEBUG] Traceback completo:")
            traceback.print_exc()
            
            return Response(
                {"detail": f"Erro ao exportar relatório: {str(e)}"},
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
        """Exportar relatório em formato CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_anotadores.csv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Cabeçalho
        writer.writerow([
            'Utilizador',
            'Nome',
            'Labels Breakdown',
            'Total de Anotações'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar label breakdown
            label_breakdown = '; '.join([f"{label}: {count}" for label, count in item.get('label_breakdown', {}).items()])
            
            # Calcular total de anotações
            total_annotations = sum(item.get('label_breakdown', {}).values())
            
            writer.writerow([
                item.get('annotator_username', 'N/A'),
                item.get('annotator_name', 'N/A'),
                label_breakdown,
                total_annotations
            ])
        
        return response

    def _export_tsv(self, report_data):
        """Exportar relatório em formato TSV"""
        response = HttpResponse(content_type='text/tab-separated-values; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_anotadores.tsv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response, delimiter='\t')
        
        # Cabeçalho
        writer.writerow([
            'Utilizador',
            'Nome',
            'Labels Breakdown',
            'Total de Anotações'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar label breakdown
            label_breakdown = '; '.join([f"{label}: {count}" for label, count in item.get('label_breakdown', {}).items()])
            
            # Calcular total de anotações
            total_annotations = sum(item.get('label_breakdown', {}).values())
            
            writer.writerow([
                item.get('annotator_username', 'N/A'),
                item.get('annotator_name', 'N/A'),
                label_breakdown,
                total_annotations
            ])
        
        return response

    def _export_pdf(self, report_data):
        """Exportar relatório em formato PDF"""
        try:
            import io
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.lib.units import inch

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
            
            # Elementos do documento
            elements = []
            
            # Título do relatório
            elements.append(Paragraph("Relatório sobre Anotadores", styles['TitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Obter informações do projeto
            project_name = "N/A"
            project_type = "N/A"
            if report_data.get('data') and len(report_data['data']) > 0:
                first_item = report_data['data'][0]
                project_name = first_item.get('project_name', "N/A")
                project_type = first_item.get('project_type', "N/A")
            
            # Informações do projeto
            elements.append(Paragraph(f"Projeto: {project_name}", styles['SubtitleStyle']))
            elements.append(Paragraph(f"Tipo: {project_type}", styles['SubtitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Adicionar informações sobre os filtros utilizados
            elements.append(Paragraph("Filtros aplicados:", styles['SubtitleStyle']))
            
            # Recuperar os filtros da query string original
            query_params = getattr(self.request, 'query_params', self.request.GET)
            
            # Usuários - converter IDs para nomes
            if 'user_ids' in query_params and query_params['user_ids']:
                try:
                    from django.contrib.auth.models import User
                    user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                    users = User.objects.filter(id__in=user_ids)
                    user_names = [user.username for user in users]
                    elements.append(Paragraph(f"Utilizadores: {', '.join(user_names)}", styles['Normal']))
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar user_ids: {e}")
                    elements.append(Paragraph(f"Utilizadores: {query_params['user_ids']}", styles['Normal']))
            
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
                    
                    elements.append(Paragraph(f"Labels: {', '.join(label_names)}", styles['Normal']))
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar label_ids: {e}")
                    elements.append(Paragraph(f"Labels: {query_params['label_ids']}", styles['Normal']))
            
            # Datasets
            if 'dataset_names' in query_params and query_params['dataset_names']:
                elements.append(Paragraph(f"Datasets: {query_params['dataset_names']}", styles['Normal']))
            
            elements.append(Spacer(1, 20))
            
            # Preparar dados para tabela principal
            table_data = [
                ['Utilizador', 'Nome', 'Total por Label', 'Labels por Dataset']
            ]
            
            # Adicionar dados à tabela
            data_items = report_data.get('data', [])
            print(f"[PDF DEBUG] Processando {len(data_items)} itens para tabela")
            
            for i, item in enumerate(data_items):
                try:
                    # Formatar breakdown de labels totais
                    label_breakdown = item.get('label_breakdown', {})
                    total_labels_text = ""
                    if label_breakdown:
                        label_parts = []
                        for label, count in label_breakdown.items():
                            label_parts.append(f"{label}: {count}")
                        total_labels_text = "; ".join(label_parts)
                    else:
                        total_labels_text = "Nenhuma label"
                    
                    # Formatar breakdown de labels por dataset
                    dataset_breakdown = item.get('dataset_label_breakdown', {})
                    dataset_labels_text = ""
                    if dataset_breakdown:
                        dataset_parts = []
                        for dataset, labels in dataset_breakdown.items():
                            if labels:
                                label_list = ", ".join(labels.keys())
                                dataset_parts.append(f"{dataset}: {label_list}")
                        dataset_labels_text = "; ".join(dataset_parts)
                    else:
                        dataset_labels_text = "Nenhuma anotação"
                    
                    # Truncar textos se muito longos
                    if len(total_labels_text) > 100:
                        total_labels_text = total_labels_text[:97] + "..."
                    if len(dataset_labels_text) > 150:
                        dataset_labels_text = dataset_labels_text[:147] + "..."
                    
                    # Truncar nome se muito longo
                    name = item.get('annotator_name', 'N/A')
                    if len(name) > 25:
                        name = name[:22] + '...'
                    
                    table_data.append([
                        item.get('annotator_username', 'N/A'),
                        name,
                        total_labels_text,
                        dataset_labels_text
                    ])
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar item {i}: {e}")
                    table_data.append([
                        'Erro',
                        'Erro ao processar',
                        'Erro',
                        'Erro'
                    ])
            
            print(f"[PDF DEBUG] Tabela criada com {len(table_data)} linhas")
            
            # Criar tabela com larguras específicas
            col_widths = [1.5*inch, 2*inch, 3*inch, 4*inch]  # Ajustar larguras das colunas
            table = Table(table_data, repeatRows=1, colWidths=col_widths)
            
            # Estilo da tabela
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Dados
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('WORDWRAP', (0, 1), (-1, -1), True),
                ('LEFTPADDING', (0, 1), (-1, -1), 3),
                ('RIGHTPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ])
            
            # Adicionar linhas alternadas
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
            
            table.setStyle(table_style)
            
            # Adicionar tabela ao documento
            elements.append(table)
            
            # Adicionar resumo no final
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Resumo:", styles['SubtitleStyle']))
            elements.append(Paragraph(f"Total de anotadores: {len(data_items)}", styles['Normal']))
            
            # Calcular estatísticas gerais
            total_annotations = 0
            all_labels = set()
            all_datasets = set()
            
            for item in data_items:
                label_breakdown = item.get('label_breakdown', {})
                total_annotations += sum(label_breakdown.values())
                all_labels.update(label_breakdown.keys())
                
                dataset_breakdown = item.get('dataset_label_breakdown', {})
                all_datasets.update(dataset_breakdown.keys())
            
            elements.append(Paragraph(f"Total de anotações: {total_annotations}", styles['Normal']))
            elements.append(Paragraph(f"Labels únicas utilizadas: {len(all_labels)}", styles['Normal']))
            elements.append(Paragraph(f"Datasets com anotações: {len(all_datasets)}", styles['Normal']))
            
            print(f"[PDF DEBUG] Construindo documento PDF...")
            
            # Construir documento
            doc.build(elements)
            
            print(f"[PDF DEBUG] PDF construído com sucesso")
            
            # Preparar resposta
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="relatorio_anotadores.pdf"'
            
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
            
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar relatório: {str(e)}"},
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
        operation_description="Exportar relatório sobre anotações em CSV, PDF ou TSV",
        query_serializer=AnnotationReportFilterSerializer,
        manual_parameters=[
            openapi.Parameter(
                'export_format',
                openapi.IN_QUERY,
                description="Formato de exportação: csv, pdf ou tsv",
                type=openapi.TYPE_STRING,
                enum=['csv', 'pdf', 'tsv'],
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
        
        if export_format not in ['csv', 'pdf', 'tsv']:
            return Response(
                {"detail": "Formato inválido. Use: csv, pdf ou tsv"},
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
            print(f"[EXPORT DEBUG] Chamando AnnotationReportService.get_report com max_results={max_results}")
            report_data = AnnotationReportService.get_report(
                **validated_data,
                page=1,
                page_size=max_results
            )
            print(f"[EXPORT DEBUG] Relatório gerado: {len(report_data.get('data', []))} itens")
            
            # Verificar se há dados para exportar
            if not report_data.get('data'):
                return Response(
                    {"detail": "Nenhum dado encontrado para exportar com os filtros especificados"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Exportar no formato solicitado
            if export_format == 'csv':
                return self._export_csv(report_data)
            elif export_format == 'pdf':
                return self._export_pdf(report_data)
            elif export_format == 'tsv':
                return self._export_tsv(report_data)
            
        except Exception as e:
            print(f"[EXPORT DEBUG] ERRO ao exportar relatório:")
            print(f"[EXPORT DEBUG] Tipo do erro: {type(e).__name__}")
            print(f"[EXPORT DEBUG] Mensagem: {str(e)}")
            import traceback
            print(f"[EXPORT DEBUG] Traceback completo:")
            traceback.print_exc()
            
            return Response(
                {"detail": f"Erro ao exportar relatório: {str(e)}"},
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
        """Exportar relatório em formato CSV"""
        print(f"[CSV DEBUG] Iniciando exportação CSV com {len(report_data.get('data', []))} itens")
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_anotacoes.csv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Obter informações do projeto (assumindo que todas as anotações são do mesmo projeto)
        project_name = ""
        project_type = ""
        if report_data.get('data') and len(report_data['data']) > 0:
            project_name = report_data['data'][0].get('project_name', "")
            project_type = report_data['data'][0].get('project_type', "")
        
        # Adicionar cabeçalho com informações do projeto
        writer.writerow(['Relatório de Anotações'])
        writer.writerow(['Projeto:', project_name])
        writer.writerow(['Tipo:', project_type])
        
        # Adicionar informações sobre os filtros utilizados
        writer.writerow(['Filtros aplicados:'])
        
        # Recuperar os filtros da query string original
        request = getattr(self, 'request', None)
        if request:
            query_params = getattr(request, 'query_params', getattr(request, 'GET', {}))
        else:
            query_params = {}
        
        # Usuários - converter IDs para nomes
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                from django.contrib.auth.models import User
                user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                users = User.objects.filter(id__in=user_ids)
                user_names = [user.username for user in users]
                writer.writerow(['Utilizadores:', ', '.join(user_names)])
            except Exception:
                writer.writerow(['Utilizadores:', query_params['user_ids']])
        
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
                label_names.extend([f"category: {label.text}" for label in category_labels])
                label_names.extend([f"span: {label.text}" for label in span_labels])
                label_names.extend([f"relation: {label.text}" for label in relation_labels])
                
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
                        example_names.append(f"Exemplo {example.id}")
                
                writer.writerow(['Exemplos:', ', '.join(example_names)])
            except Exception:
                writer.writerow(['Exemplos:', query_params['example_ids']])
        
        # Filtro de discrepâncias
        if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
            discrepancy_map = {
                'all': 'Todas as anotações',
                'with_discrepancy': 'Apenas com discrepâncias',
                'without_discrepancy': 'Apenas sem discrepâncias'
            }
            writer.writerow(['Filtro de Discrepâncias:', discrepancy_map.get(query_params['discrepancy_filter'], query_params['discrepancy_filter'])])
        
        # Tipos de anotação
        if 'annotation_types' in query_params and query_params['annotation_types']:
            annotation_types = [t.strip() for t in query_params['annotation_types'].split(',') if t.strip()]
            writer.writerow(['Tipos de Anotação:', ', '.join(annotation_types)])
        
        # Perguntas da perspectiva
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                from projects.models import Question
                question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                questions = Question.objects.filter(id__in=question_ids)
                question_texts = [q.question for q in questions]
                writer.writerow(['Perguntas da Perspectiva:', ', '.join(question_texts)])
            except Exception:
                writer.writerow(['Perguntas da Perspectiva:', query_params['perspective_question_ids']])
        
        # Respostas da perspectiva
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                from projects.models import Answer
                answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                answers = Answer.objects.filter(id__in=answer_ids)
                answer_texts = [a.answer_text or a.answer_option or f"Resposta {a.id}" for a in answers]
                writer.writerow(['Respostas da Perspectiva:', ', '.join(answer_texts)])
            except Exception:
                writer.writerow(['Respostas da Perspectiva:', query_params['perspective_answer_ids']])
        
        # Filtros de data
        if 'date_from' in query_params and query_params['date_from']:
            writer.writerow(['Data de Início:', query_params['date_from']])
        
        if 'date_to' in query_params and query_params['date_to']:
            writer.writerow(['Data de Fim:', query_params['date_to']])
        
        # Número máximo de resultados
        if 'max_results' in query_params and query_params['max_results']:
            writer.writerow(['Máximo de Resultados:', query_params['max_results']])
        
        writer.writerow([])  # Linha em branco
        
        # Cabeçalho da tabela
        writer.writerow([
            'Exemplo',
            'Utilizador',
            'Label',
            'Data Criação',
            'Detalhes'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        print(f"[CSV DEBUG] Processando {len(data_items)} itens de dados")
        
        for i, item in enumerate(data_items):
            try:
                # Formatar detalhes como string JSON simplificada
                detail_str = ""
                if item.get('detail'):
                    detail_str = "; ".join([f"{k}: {v}" for k, v in item['detail'].items()])
                
                # Formatar data (agora é uma string ISO)
                date_str = '-'
                if item.get('created_at'):
                    # Se já for string, usar diretamente ou formatar
                    try:
                        from datetime import datetime
                        # Tentar converter para datetime e formatar
                        dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, AttributeError, TypeError):
                        # Se falhar, usar a string original
                        date_str = str(item['created_at'])
                
                # Garantir que todos os campos são strings
                example_name = str(item.get('example_name', '-'))
                username = str(item.get('username', '-'))
                label_text = str(item.get('label_text', '-'))
                
                writer.writerow([
                    example_name,
                    username,
                    label_text,
                    date_str,
                    detail_str
                ])
                
                if i < 3:  # Debug apenas os primeiros 3 itens
                    print(f"[CSV DEBUG] Item {i}: {example_name}, {username}, {label_text}")
                    
            except Exception as e:
                print(f"[CSV DEBUG] Erro ao processar item {i}: {e}")
                # Escrever linha de erro
                writer.writerow([
                    'Erro ao processar',
                    'Erro',
                    'Erro',
                    'Erro',
                    f'Erro: {str(e)}'
                ])
        
        return response

    def _export_tsv(self, report_data):
        """Exportar relatório em formato TSV"""
        response = HttpResponse(content_type='text/tab-separated-values; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_anotacoes.tsv"'
        
        # Adicionar BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response, delimiter='\t')
        
        # Obter informações do projeto (assumindo que todas as anotações são do mesmo projeto)
        project_name = ""
        project_type = ""
        if report_data.get('data') and len(report_data['data']) > 0:
            project_name = report_data['data'][0].get('project_name', "")
            project_type = report_data['data'][0].get('project_type', "")
        
        # Adicionar cabeçalho com informações do projeto
        writer.writerow(['Relatório de Anotações'])
        writer.writerow(['Projeto:', project_name])
        writer.writerow(['Tipo:', project_type])
        
        # Adicionar informações sobre os filtros utilizados
        writer.writerow(['Filtros aplicados:'])
        
        # Recuperar os filtros da query string original
        request = getattr(self, 'request', None)
        if request:
            query_params = getattr(request, 'query_params', getattr(request, 'GET', {}))
        else:
            query_params = {}
        
        # Usuários - converter IDs para nomes
        if 'user_ids' in query_params and query_params['user_ids']:
            try:
                from django.contrib.auth.models import User
                user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                users = User.objects.filter(id__in=user_ids)
                user_names = [user.username for user in users]
                writer.writerow(['Utilizadores:', ', '.join(user_names)])
            except Exception:
                writer.writerow(['Utilizadores:', query_params['user_ids']])
        
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
                        example_names.append(f"Exemplo {example.id}")
                
                writer.writerow(['Exemplos:', ', '.join(example_names)])
            except Exception:
                writer.writerow(['Exemplos:', query_params['example_ids']])
        
        # Filtro de discrepâncias
        if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
            discrepancy_map = {
                'all': 'Todas as anotações',
                'with_discrepancy': 'Apenas com discrepâncias',
                'without_discrepancy': 'Apenas sem discrepâncias'
            }
            writer.writerow(['Filtro de Discrepâncias:', discrepancy_map.get(query_params['discrepancy_filter'], query_params['discrepancy_filter'])])
        
        # Perguntas da perspectiva
        if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
            try:
                from projects.models import Question
                question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                questions = Question.objects.filter(id__in=question_ids)
                question_texts = [q.question for q in questions]
                writer.writerow(['Perguntas da Perspectiva:', ', '.join(question_texts)])
            except Exception:
                writer.writerow(['Perguntas da Perspectiva:', query_params['perspective_question_ids']])
        
        # Respostas da perspectiva
        if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
            try:
                from projects.models import Answer
                answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                answers = Answer.objects.filter(id__in=answer_ids)
                answer_texts = [a.answer_text or a.answer_option or f"Resposta {a.id}" for a in answers]
                writer.writerow(['Respostas da Perspectiva:', ', '.join(answer_texts)])
            except Exception:
                writer.writerow(['Respostas da Perspectiva:', query_params['perspective_answer_ids']])
        
        writer.writerow([])  # Linha em branco
        
        # Cabeçalho da tabela
        writer.writerow([
            'Exemplo',
            'Utilizador',
            'Label',
            'Data Criação',
            'Detalhes'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar detalhes como string JSON simplificada
            detail_str = ""
            if item['detail']:
                detail_str = "; ".join([f"{k}: {v}" for k, v in item['detail'].items()])
            
            # Formatar data (agora é uma string ISO)
            date_str = '-'
            if item['created_at']:
                # Se já for string, usar diretamente ou formatar
                try:
                    from datetime import datetime
                    # Tentar converter para datetime e formatar
                    dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except (ValueError, AttributeError, TypeError):
                    # Se falhar, usar a string original
                    date_str = item['created_at']
            
            writer.writerow([
                item['example_name'],
                item['username'],
                item['label_text'] or '-',
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
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.lib.units import inch

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
            
            # Elementos do documento
            elements = []
            
            # Título do relatório
            elements.append(Paragraph("Relatório sobre Anotações", styles['TitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Obter informações do projeto
            project_name = "N/A"
            project_type = "N/A"
            if report_data.get('data') and len(report_data['data']) > 0:
                first_item = report_data['data'][0]
                project_name = first_item.get('project_name', "N/A")
                project_type = first_item.get('project_type', "N/A")
            
            # Informações do projeto
            elements.append(Paragraph(f"Projeto: {project_name}", styles['SubtitleStyle']))
            elements.append(Paragraph(f"Tipo: {project_type}", styles['SubtitleStyle']))
            elements.append(Spacer(1, 10))
            
            # Adicionar informações sobre os filtros utilizados
            elements.append(Paragraph("Filtros aplicados:", styles['SubtitleStyle']))
            
            # Recuperar os filtros da query string original
            request = getattr(self, 'request', None)
            if request:
                query_params = getattr(request, 'query_params', getattr(request, 'GET', {}))
            else:
                query_params = {}
            
            # Usuários - converter IDs para nomes
            if 'user_ids' in query_params and query_params['user_ids']:
                try:
                    from django.contrib.auth.models import User
                    user_ids = [int(uid.strip()) for uid in query_params['user_ids'].split(',') if uid.strip()]
                    users = User.objects.filter(id__in=user_ids)
                    user_names = [user.username for user in users]
                    elements.append(Paragraph(f"Utilizadores: {', '.join(user_names)}", styles['Normal']))
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar user_ids: {e}")
                    elements.append(Paragraph(f"Utilizadores: {query_params['user_ids']}", styles['Normal']))
            
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
                    
                    elements.append(Paragraph(f"Labels: {', '.join(label_names)}", styles['Normal']))
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar label_ids: {e}")
                    elements.append(Paragraph(f"Labels: {query_params['label_ids']}", styles['Normal']))
            
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
                            example_names.append(f"Exemplo {example.id}")
                    
                    elements.append(Paragraph(f"Exemplos: {', '.join(example_names)}", styles['Normal']))
                except Exception:
                    elements.append(Paragraph(f"Exemplos: {query_params['example_ids']}", styles['Normal']))
            
            # Filtro de discrepâncias
            if 'discrepancy_filter' in query_params and query_params['discrepancy_filter']:
                discrepancy_map = {
                    'all': 'Todas as anotações',
                    'with_discrepancy': 'Apenas com discrepâncias',
                    'without_discrepancy': 'Apenas sem discrepâncias'
                }
                elements.append(Paragraph(f"Filtro de Discrepâncias: {discrepancy_map.get(query_params['discrepancy_filter'], query_params['discrepancy_filter'])}", styles['Normal']))
            
            # Perguntas da perspectiva
            if 'perspective_question_ids' in query_params and query_params['perspective_question_ids']:
                try:
                    from projects.models import Question
                    question_ids = [int(qid.strip()) for qid in query_params['perspective_question_ids'].split(',') if qid.strip()]
                    questions = Question.objects.filter(id__in=question_ids)
                    question_texts = [q.question for q in questions]
                    elements.append(Paragraph(f"Perguntas da Perspectiva: {', '.join(question_texts)}", styles['Normal']))
                except Exception:
                    elements.append(Paragraph(f"Perguntas da Perspectiva: {query_params['perspective_question_ids']}", styles['Normal']))
            
            # Respostas da perspectiva
            if 'perspective_answer_ids' in query_params and query_params['perspective_answer_ids']:
                try:
                    from projects.models import Answer
                    answer_ids = [int(aid.strip()) for aid in query_params['perspective_answer_ids'].split(',') if aid.strip()]
                    answers = Answer.objects.filter(id__in=answer_ids)
                    answer_texts = [a.answer_text or a.answer_option or f"Resposta {a.id}" for a in answers]
                    elements.append(Paragraph(f"Respostas da Perspectiva: {', '.join(answer_texts)}", styles['Normal']))
                except Exception:
                    elements.append(Paragraph(f"Respostas da Perspectiva: {query_params['perspective_answer_ids']}", styles['Normal']))
            
            elements.append(Spacer(1, 20))
            
            # Preparar dados para tabela principal
            table_data = [
                ['Exemplo', 'Utilizador', 'Label', 'Data']
            ]
            
            # Adicionar dados à tabela
            data_items = report_data.get('data', [])
            print(f"[PDF DEBUG] Processando {len(data_items)} itens para tabela")
            
            for i, item in enumerate(data_items):
                try:
                    # Formatar data
                    date_str = '-'
                    if item['created_at']:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                        except (ValueError, AttributeError, TypeError):
                            date_str = item['created_at']
                    
                    # Preparar textos (sem truncar - deixar o ReportLab gerir a quebra de linha)
                    example_name = item['example_name'] or '-'
                    label_text = item['label_text'] or '-'
                    
                    # Apenas truncar se extremamente longo (mais de 100 caracteres)
                    if len(example_name) > 100:
                        example_name = example_name[:97] + "..."
                    
                    if len(label_text) > 80:
                        label_text = label_text[:77] + "..."
                    
                    table_data.append([
                        example_name,
                        item['username'],
                        label_text,
                        date_str
                    ])
                except Exception as e:
                    print(f"[PDF DEBUG] Erro ao processar item {i}: {e}")
                    table_data.append([
                        'Erro ao processar',
                        'Erro',
                        'Erro',
                        'Erro'
                    ])
            
            print(f"[PDF DEBUG] Tabela criada com {len(table_data)} linhas")
            
            # Criar tabela com larguras mais flexíveis para landscape A4
            # Landscape A4 tem aproximadamente 11.7 inches de largura útil
            col_widths = [3.5*inch, 2*inch, 3.5*inch, 2*inch]  # Larguras mais equilibradas
            table = Table(table_data, repeatRows=1, colWidths=col_widths)
            
            # Estilo da tabela
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Dados
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Aumentar ligeiramente o tamanho da fonte
                ('WORDWRAP', (0, 1), (-1, -1), True),
                ('LEFTPADDING', (0, 1), (-1, -1), 4),
                ('RIGHTPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                # Permitir que as células se expandam verticalmente conforme necessário
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ])
            
            table.setStyle(table_style)
            
            # Adicionar tabela ao documento
            elements.append(table)
            
            # Adicionar resumo no final
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Resumo:", styles['SubtitleStyle']))
            elements.append(Paragraph(f"Total de anotações: {len(data_items)}", styles['Normal']))
            
            # Calcular estatísticas gerais
            all_users = set()
            all_labels = set()
            all_examples = set()
            
            for item in data_items:
                all_users.add(item['username'])
                if item['label_text']:
                    all_labels.add(item['label_text'])
                all_examples.add(item['example_name'])
            
            elements.append(Paragraph(f"Total de utilizadores: {len(all_users)}", styles['Normal']))
            elements.append(Paragraph(f"Labels únicas utilizadas: {len(all_labels)}", styles['Normal']))
            elements.append(Paragraph(f"Exemplos únicos: {len(all_examples)}", styles['Normal']))
            
            print(f"[PDF DEBUG] Construindo documento PDF...")
            
            # Construir documento
            doc.build(elements)
            
            print(f"[PDF DEBUG] PDF construído com sucesso")
            
            # Preparar resposta
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="relatorio_anotacoes.pdf"'
            
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
