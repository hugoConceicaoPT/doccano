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
    AnnotatorReportResponseSerializer
)
from .services import AnnotatorReportService


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
                'task_types',
                openapi.IN_QUERY,
                description="Lista de tipos de tarefa (separados por vírgula, opcional)",
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
            report_data = AnnotatorReportService.get_report(**validated_data)
            
            # Serializar resposta
            response_serializer = AnnotatorReportResponseSerializer(data=report_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
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
        
        # Processar label_ids (opcional)
        if 'label_ids' in query_params and query_params['label_ids']:
            try:
                processed['label_ids'] = [
                    int(x.strip()) for x in query_params['label_ids'].split(',') if x.strip()
                ]
            except ValueError:
                processed['label_ids'] = []
        
        # Processar task_types (opcional)
        if 'task_types' in query_params and query_params['task_types']:
            processed['task_types'] = [
                x.strip() for x in query_params['task_types'].split(',') if x.strip()
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
                'task_types',
                openapi.IN_QUERY,
                description="Lista de tipos de tarefa (separados por vírgula, opcional)",
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
            report_data = AnnotatorReportService.get_report(**validated_data)
            
            # Exportar no formato solicitado
            if export_format == 'csv':
                return self._export_csv(report_data)
            elif export_format == 'pdf':
                return self._export_pdf(report_data)
            elif export_format == 'tsv':
                return self._export_tsv(report_data)
            
        except Exception as e:
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
        
        # Processar task_types (opcional)
        if 'task_types' in query_params and query_params['task_types']:
            processed['task_types'] = [
                x.strip() for x in query_params['task_types'].split(',') if x.strip()
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
            'Primeira Anotação',
            'Última Anotação',
            'Labels Breakdown'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar label breakdown
            label_breakdown = '; '.join([f"{label}: {count}" for label, count in item['label_breakdown'].items()])
            
            writer.writerow([
                item['annotator_username'],
                item['annotator_name'],
                item['first_annotation_date'].strftime('%Y-%m-%d %H:%M') if item['first_annotation_date'] else '',
                item['last_annotation_date'].strftime('%Y-%m-%d %H:%M') if item['last_annotation_date'] else '',
                label_breakdown
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
            'Primeira Anotação',
            'Última Anotação',
            'Labels Breakdown'
        ])
        
        # Dados
        data_items = report_data.get('data', [])
        
        for item in data_items:
            # Formatar label breakdown
            label_breakdown = '; '.join([f"{label}: {count}" for label, count in item['label_breakdown'].items()])
            
            writer.writerow([
                item['annotator_username'],
                item['annotator_name'],
                item['first_annotation_date'].strftime('%Y-%m-%d %H:%M') if item['first_annotation_date'] else '',
                item['last_annotation_date'].strftime('%Y-%m-%d %H:%M') if item['last_annotation_date'] else '',
                label_breakdown
            ])
        
        return response

    def _export_pdf(self, report_data):
        """Exportar relatório em formato PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_anotadores.pdf"'
        
        # Criar documento PDF
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centro
        )
        
        # Título
        title = Paragraph("Relatório sobre Anotadores", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Resumo
        summary = report_data['summary']
        summary_text = f"""
        <b>Resumo do Relatório:</b><br/>
        • Total de Anotadores: {summary['total_annotators']}<br/>
        """
        
        if summary['date_range_from'] or summary['date_range_to']:
            summary_text += "<br/><b>Período:</b><br/>"
            if summary['date_range_from']:
                summary_text += f"• De: {summary['date_range_from'].strftime('%Y-%m-%d')}<br/>"
            if summary['date_range_to']:
                summary_text += f"• Até: {summary['date_range_to'].strftime('%Y-%m-%d')}<br/>"
        
        summary_para = Paragraph(summary_text, styles['Normal'])
        elements.append(summary_para)
        elements.append(Spacer(1, 30))
        
        # Tabela de dados
        data_items = report_data.get('data', [])
        
        if data_items:
            # Cabeçalho da tabela
            table_data = [
                ['Utilizador', 'Nome', 'Primeira Anotação', 'Última Anotação']
            ]
            
            # Dados da tabela
            for item in data_items:
                table_data.append([
                    item['annotator_username'],
                    item['annotator_name'][:30] + '...' if len(item['annotator_name']) > 30 else item['annotator_name'],
                    item['first_annotation_date'].strftime('%Y-%m-%d') if item['first_annotation_date'] else '-',
                    item['last_annotation_date'].strftime('%Y-%m-%d') if item['last_annotation_date'] else '-'
                ])
            
            # Criar tabela
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        else:
            no_data = Paragraph("Nenhum dado encontrado para os filtros especificados.", styles['Normal'])
            elements.append(no_data)
        
        # Construir PDF
        doc.build(elements)
        
        return response
