from typing import Dict, List, Optional, Any
from django.db.models import Count, Q, Min, Max, Avg, Case, When, IntegerField
from django.contrib.auth.models import User
from django.utils import timezone
from collections import defaultdict

from labels.models import Category, Span, TextLabel, Relation
from projects.models import Project
from label_types.models import CategoryType, SpanType, RelationType


class AnnotatorReportService:
    """Service para geração de relatórios sobre anotadores"""

    @staticmethod
    def get_report(
        project_ids: List[int],
        user_ids: Optional[List[int]] = None,
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None,
        task_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gera relatório sobre anotadores com filtros especificados
        
        Args:
            project_ids: Lista de IDs dos projetos
            user_ids: Lista de IDs dos utilizadores (opcional)
            date_from: Data de início (opcional)
            date_to: Data de fim (opcional)
            label_ids: Lista de IDs dos rótulos (opcional)
            task_types: Lista de tipos de tarefa (opcional)
            
        Returns:
            Dicionário com summary e data do relatório
        """
        
        # Obter dados agregados por utilizador
        annotator_data = AnnotatorReportService._get_annotator_data(
            project_ids, user_ids, date_from, date_to, label_ids, task_types
        )
        
        # Calcular breakdown de rótulos para cada anotador
        for annotator in annotator_data:
            annotator['label_breakdown'] = AnnotatorReportService._get_label_breakdown(
                annotator['annotator_id'], project_ids, date_from, date_to, label_ids
            )
        
        # Calcular resumo geral
        summary = AnnotatorReportService._calculate_summary(
            annotator_data, date_from, date_to
        )
        
        result = {
            'summary': summary,
            'data': annotator_data
        }
        
        return result

    @staticmethod
    def _get_annotator_data(
        project_ids: List[int],
        user_ids: Optional[List[int]] = None,
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None,
        task_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Obter dados agregados por anotador"""
        
        # Base query para filtrar por projeto
        base_filter = Q(example__project_id__in=project_ids)
        
        # Aplicar filtros de data
        if date_from:
            base_filter &= Q(created_at__gte=date_from)
        if date_to:
            base_filter &= Q(created_at__lte=date_to)
        
        # Aplicar filtro de utilizadores
        if user_ids:
            base_filter &= Q(user_id__in=user_ids)
        
        # Obter dados de Categories
        categories_filter = base_filter
        if label_ids:
            # Verificar se existem CategoryTypes nos label_ids
            category_type_ids = CategoryType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if category_type_ids:
                categories_filter &= Q(label_id__in=category_type_ids)
            else:
                # Se não há CategoryTypes nos label_ids, não incluir categories
                categories_filter = Q(pk__isnull=True)
        
        categories_data = (
            Category.objects
            .filter(categories_filter)
            .values('user_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
            .annotate(
                categories_count=Count('id'),
                first_annotation=Min('created_at'),
                last_annotation=Max('created_at')
            )
        )
        
        # Obter dados de Spans
        spans_filter = base_filter
        if label_ids:
            # Verificar se existem SpanTypes nos label_ids
            span_type_ids = SpanType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if span_type_ids:
                spans_filter &= Q(label_id__in=span_type_ids)
            else:
                # Se não há SpanTypes nos label_ids, não incluir spans
                spans_filter = Q(pk__isnull=True)
        
        spans_data = (
            Span.objects
            .filter(spans_filter)
            .values('user_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
            .annotate(
                spans_count=Count('id'),
                first_annotation=Min('created_at'),
                last_annotation=Max('created_at')
            )
        )
        
        # Obter dados de TextLabels (não têm label específico)
        texts_filter = base_filter
        if label_ids:
            # TextLabels não têm labels específicos, então se label_ids está definido, excluir
            texts_filter = Q(pk__isnull=True)
        
        texts_data = (
            TextLabel.objects
            .filter(texts_filter)
            .values('user_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
            .annotate(
                texts_count=Count('id'),
                first_annotation=Min('created_at'),
                last_annotation=Max('created_at')
            )
        )
        
        # Obter dados de Relations
        relations_filter = base_filter
        if label_ids:
            # Verificar se existem RelationTypes nos label_ids
            relation_type_ids = RelationType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if relation_type_ids:
                relations_filter &= Q(type_id__in=relation_type_ids)
            else:
                # Se não há RelationTypes nos label_ids, não incluir relations
                relations_filter = Q(pk__isnull=True)
        
        relations_data = (
            Relation.objects
            .filter(relations_filter)
            .values('user_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
            .annotate(
                relations_count=Count('id'),
                first_annotation=Min('created_at'),
                last_annotation=Max('created_at')
            )
        )
        
        # Consolidar dados por utilizador
        user_data = defaultdict(lambda: {
            'annotator_id': None,
            'annotator_username': '',
            'annotator_name': '',
            'first_annotation_date': None,
            'last_annotation_date': None
        })
        
        # Processar todos os dados para obter informações básicas dos utilizadores
        all_data = list(categories_data) + list(spans_data) + list(texts_data) + list(relations_data)
        
        for item in all_data:
            user_id = item['user_id']
            user_data[user_id].update({
                'annotator_id': user_id,
                'annotator_username': item['user__username'],
                'annotator_name': AnnotatorReportService._format_user_name(
                    item['user__first_name'], item['user__last_name'], item['user__username']
                ),
                'first_annotation_date': AnnotatorReportService._min_date(
                    user_data[user_id]['first_annotation_date'], item.get('first_annotation')
                ),
                'last_annotation_date': AnnotatorReportService._max_date(
                    user_data[user_id]['last_annotation_date'], item.get('last_annotation')
                )
            })
        
        # Converter para lista
        result = list(user_data.values())
        
        # Ordenar por nome do utilizador
        result.sort(key=lambda x: x['annotator_username'])
        
        return result

    @staticmethod
    def _get_label_breakdown(
        user_id: int,
        project_ids: List[int],
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None
    ) -> Dict[str, int]:
        """Obter breakdown de rótulos para um utilizador específico"""
        
        base_filter = Q(user_id=user_id, example__project_id__in=project_ids)
        
        if date_from:
            base_filter &= Q(created_at__gte=date_from)
        if date_to:
            base_filter &= Q(created_at__lte=date_to)
        
        breakdown = {}
        
        # Categories breakdown
        category_filter = base_filter
        if label_ids:
            category_type_ids = CategoryType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if category_type_ids:
                category_filter &= Q(label_id__in=category_type_ids)
            else:
                category_filter = Q(pk__isnull=True)
        
        categories = (
            Category.objects
            .filter(category_filter)
            .values('label__text')
            .annotate(count=Count('id'))
        )
        
        for item in categories:
            breakdown[item['label__text']] = item['count']
        
        # Spans breakdown
        span_filter = base_filter
        if label_ids:
            span_type_ids = SpanType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if span_type_ids:
                span_filter &= Q(label_id__in=span_type_ids)
            else:
                span_filter = Q(pk__isnull=True)
        
        spans = (
            Span.objects
            .filter(span_filter)
            .values('label__text')
            .annotate(count=Count('id'))
        )
        
        for item in spans:
            label_text = item['label__text']
            if label_text in breakdown:
                breakdown[label_text] += item['count']
            else:
                breakdown[label_text] = item['count']
        
        # Relations breakdown
        relation_filter = base_filter
        if label_ids:
            relation_type_ids = RelationType.objects.filter(id__in=label_ids).values_list('id', flat=True)
            if relation_type_ids:
                relation_filter &= Q(type_id__in=relation_type_ids)
            else:
                relation_filter = Q(pk__isnull=True)
        
        relations = (
            Relation.objects
            .filter(relation_filter)
            .values('type__text')
            .annotate(count=Count('id'))
        )
        
        for item in relations:
            label_text = item['type__text']
            if label_text in breakdown:
                breakdown[label_text] += item['count']
            else:
                breakdown[label_text] = item['count']
        
        return breakdown

    @staticmethod
    def _calculate_summary(
        annotator_data: List[Dict[str, Any]],
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None
    ) -> Dict[str, Any]:
        """Calcular resumo geral do relatório"""
        
        total_annotators = len(annotator_data)
        
        return {
            'total_annotators': total_annotators,
            'date_range_from': date_from,
            'date_range_to': date_to
        }

    @staticmethod
    def _format_user_name(first_name: str, last_name: str, username: str) -> str:
        """Formatar nome do utilizador"""
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return username

    @staticmethod
    def _min_date(date1, date2):
        """Retornar a data mínima entre duas datas"""
        if date1 is None:
            return date2
        if date2 is None:
            return date1
        return min(date1, date2)

    @staticmethod
    def _max_date(date1, date2):
        """Retornar a data máxima entre duas datas"""
        if date1 is None:
            return date2
        if date2 is None:
            return date1
        return max(date1, date2) 