from typing import Dict, List, Optional, Any
from django.db.models import Count, Q, Min, Max, Avg, Case, When, IntegerField
from django.contrib.auth.models import User
from django.utils import timezone
from collections import defaultdict

from labels.models import Category, Span, TextLabel, Relation
from projects.models import Project, Member
from label_types.models import CategoryType, SpanType, RelationType
from examples.models import Example


class AnnotatorReportService:
    """Service para geração de relatórios sobre anotadores"""

    @staticmethod
    def get_report(
        project_ids: List[int],
        user_ids: Optional[List[int]] = None,
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None,
        perspective_ids: Optional[List[int]] = None,
        dataset_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gera relatório sobre anotadores com filtros especificados
        
        Args:
            project_ids: Lista de IDs dos projetos
            user_ids: Lista de IDs dos utilizadores (opcional)
            date_from: Data de início (opcional)
            date_to: Data de fim (opcional)
            label_ids: Lista de IDs dos rótulos (opcional)
            perspective_ids: Lista de IDs das perspectivas (opcional)
            
        Returns:
            Dicionário com summary e data do relatório
        """
        
        # Obter dados agregados por utilizador
        annotator_data = AnnotatorReportService._get_annotator_data(
            project_ids, user_ids, date_from, date_to, label_ids, perspective_ids, dataset_names
        )
        
        # Calcular breakdown de rótulos para cada anotador
        for annotator in annotator_data:
            annotator['label_breakdown'] = AnnotatorReportService._get_label_breakdown(
                annotator['annotator_id'], project_ids, date_from, date_to, label_ids, perspective_ids, dataset_names
            )
            # Adicionar informação detalhada sobre labels por dataset
            annotator['dataset_label_breakdown'] = AnnotatorReportService._get_dataset_label_breakdown(
                annotator['annotator_id'], project_ids, date_from, date_to, label_ids, perspective_ids, dataset_names
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
        perspective_ids: Optional[List[int]] = None,
        dataset_names: Optional[List[str]] = None
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
        
        # Aplicar filtro de datasets
        if dataset_names:
            base_filter &= Q(example__upload_name__in=dataset_names)
        
        # Aplicar filtro de perspectivas - obter utilizadores das perspectivas especificadas
        if perspective_ids:
            # Obter IDs dos utilizadores que pertencem às perspectivas especificadas
            perspective_user_ids = Member.objects.filter(
                perspective_id__in=perspective_ids,
                project_id__in=project_ids
            ).values_list('user_id', flat=True)
            
            if perspective_user_ids:
                base_filter &= Q(user_id__in=perspective_user_ids)
            else:
                # Se não há utilizadores nas perspectivas especificadas, retornar vazio
                return []

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
            .annotate(categories_count=Count('id'))
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
            .annotate(spans_count=Count('id'))
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
            .annotate(texts_count=Count('id'))
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
            .annotate(relations_count=Count('id'))
        )
        
        # Consolidar dados por utilizador
        user_data = defaultdict(lambda: {
            'annotator_id': None,
            'annotator_username': '',
            'annotator_name': ''
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
        label_ids: Optional[List[int]] = None,
        perspective_ids: Optional[List[int]] = None,
        dataset_names: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Obter breakdown de rótulos para um utilizador específico"""
        
        try:
            base_filter = Q(user_id=user_id, example__project_id__in=project_ids)
            
            if date_from:
                base_filter &= Q(created_at__gte=date_from)
            if date_to:
                base_filter &= Q(created_at__lte=date_to)
            
            # Aplicar filtro de datasets
            if dataset_names:
                base_filter &= Q(example__upload_name__in=dataset_names)
            
            # Aplicar filtro de perspectivas - verificar se o utilizador pertence às perspectivas especificadas
            if perspective_ids:
                # Verificar se o utilizador pertence a alguma das perspectivas especificadas
                user_in_perspectives = Member.objects.filter(
                    user_id=user_id,
                    perspective_id__in=perspective_ids,
                    project_id__in=project_ids
                ).exists()
                
                if not user_in_perspectives:
                    # Se o utilizador não pertence às perspectivas especificadas, retornar vazio
                    return {}
            
            breakdown = {}
            
            # Categories breakdown
            try:
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
                    label_text = item.get('label__text')
                    count = item.get('count', 0)
                    if label_text and count > 0:
                        breakdown[label_text] = count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar categories breakdown: {e}")
            
            # Spans breakdown
            try:
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
                    label_text = item.get('label__text')
                    count = item.get('count', 0)
                    if label_text and count > 0:
                        if label_text in breakdown:
                            breakdown[label_text] += count
                        else:
                            breakdown[label_text] = count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar spans breakdown: {e}")
            
            # Relations breakdown
            try:
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
                    label_text = item.get('type__text')
                    count = item.get('count', 0)
                    if label_text and count > 0:
                        if label_text in breakdown:
                            breakdown[label_text] += count
                        else:
                            breakdown[label_text] = count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar relations breakdown: {e}")
            
            return breakdown
            
        except Exception as e:
            print(f"[DEBUG] Erro geral em _get_label_breakdown: {e}")
            import traceback
            traceback.print_exc()
            return {}

    @staticmethod
    def _get_dataset_label_breakdown(
        user_id: int,
        project_ids: List[int],
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None,
        perspective_ids: Optional[List[int]] = None,
        dataset_names: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, int]]:
        """Obter breakdown detalhado de labels por dataset para o utilizador"""
        
        try:
            base_filter = Q(user_id=user_id, example__project_id__in=project_ids)
            
            if date_from:
                base_filter &= Q(created_at__gte=date_from)
            if date_to:
                base_filter &= Q(created_at__lte=date_to)
            
            # Aplicar filtro de datasets
            if dataset_names:
                base_filter &= Q(example__upload_name__in=dataset_names)
            
            # Aplicar filtro de perspectivas
            if perspective_ids:
                user_in_perspectives = Member.objects.filter(
                    user_id=user_id,
                    perspective_id__in=perspective_ids,
                    project_id__in=project_ids
                ).exists()
                
                if not user_in_perspectives:
                    return {}
            
            result = defaultdict(lambda: defaultdict(int))
            
            # Categories
            try:
                category_filter = base_filter
                if label_ids:
                    category_type_ids = CategoryType.objects.filter(id__in=label_ids).values_list('id', flat=True)
                    if category_type_ids:
                        category_filter &= Q(label_id__in=category_type_ids)
                    else:
                        category_filter = Q(pk__isnull=True)  # Não incluir se não há CategoryTypes nos label_ids
                
                categories = (
                    Category.objects
                    .filter(category_filter)
                    .select_related('label', 'example')
                    .values('example__upload_name', 'label__text')
                    .annotate(count=Count('id'))
                )
                
                for item in categories:
                    upload_name = item.get('example__upload_name')
                    label_text = item.get('label__text')
                    count = item.get('count', 0)
                    
                    if upload_name and label_text and count > 0:
                        result[upload_name][label_text] += count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar categories: {e}")
            
            # Spans
            try:
                span_filter = base_filter
                if label_ids:
                    span_type_ids = SpanType.objects.filter(id__in=label_ids).values_list('id', flat=True)
                    if span_type_ids:
                        span_filter &= Q(label_id__in=span_type_ids)
                    else:
                        span_filter = Q(pk__isnull=True)  # Não incluir se não há SpanTypes nos label_ids
                
                spans = (
                    Span.objects
                    .filter(span_filter)
                    .select_related('label', 'example')
                    .values('example__upload_name', 'label__text')
                    .annotate(count=Count('id'))
                )
                
                for item in spans:
                    upload_name = item.get('example__upload_name')
                    label_text = item.get('label__text')
                    count = item.get('count', 0)
                    
                    if upload_name and label_text and count > 0:
                        result[upload_name][label_text] += count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar spans: {e}")
            
            # Relations
            try:
                relation_filter = base_filter
                if label_ids:
                    relation_type_ids = RelationType.objects.filter(id__in=label_ids).values_list('id', flat=True)
                    if relation_type_ids:
                        relation_filter &= Q(type_id__in=relation_type_ids)
                    else:
                        relation_filter = Q(pk__isnull=True)  # Não incluir se não há RelationTypes nos label_ids
                
                relations = (
                    Relation.objects
                    .filter(relation_filter)
                    .select_related('type', 'example')
                    .values('example__upload_name', 'type__text')
                    .annotate(count=Count('id'))
                )
                
                for item in relations:
                    upload_name = item.get('example__upload_name')
                    type_text = item.get('type__text')
                    count = item.get('count', 0)
                    
                    if upload_name and type_text and count > 0:
                        result[upload_name][type_text] += count
            except Exception as e:
                print(f"[DEBUG] Erro ao processar relations: {e}")
            
            # Converter defaultdict para dict normal
            return {dataset: dict(labels) for dataset, labels in result.items()}
            
        except Exception as e:
            print(f"[DEBUG] Erro geral em _get_dataset_label_breakdown: {e}")
            import traceback
            traceback.print_exc()
            return {}

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


class AnnotationReportService:
    """Service para geração de relatórios sobre anotações"""
    
    ANNOTATION_TYPES = {
        'category': Category,
        'span': Span,
        'text': TextLabel,
        'relation': Relation,
    }
    
    @staticmethod
    def get_report(
        project_ids: List[int],
        user_ids: Optional[List[int]] = None,
        example_ids: Optional[List[int]] = None,
        date_from: Optional[timezone.datetime] = None,
        date_to: Optional[timezone.datetime] = None,
        label_ids: Optional[List[int]] = None,
        annotation_types: Optional[List[str]] = None,
        discrepancy_filter: Optional[str] = None,
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Gera relatório sobre anotações com filtros especificados
        
        Args:
            project_ids: Lista de IDs dos projetos
            user_ids: Lista de IDs dos utilizadores (opcional)
            example_ids: Lista de IDs dos exemplos (opcional)
            date_from: Data de início (opcional)
            date_to: Data de fim (opcional)
            label_ids: Lista de IDs dos rótulos (opcional)
            annotation_types: Lista de tipos de anotação (opcional)
            discrepancy_filter: Filtro de discrepâncias: all, with_discrepancy, without_discrepancy (opcional)
            perspective_question_ids: Lista de IDs das perguntas da perspectiva (opcional)
            perspective_answer_ids: Lista de IDs das respostas da perspectiva (opcional)
            page: Página dos resultados para paginação
            page_size: Tamanho da página para paginação
            
        Returns:
            Dicionário com summary e data do relatório
        """
        
        # Se annotation_types não for especificado, usar todos
        if not annotation_types:
            annotation_types = list(AnnotationReportService.ANNOTATION_TYPES.keys())
        
        # Filtrar apenas tipos de anotação válidos
        valid_types = [t for t in annotation_types if t in AnnotationReportService.ANNOTATION_TYPES]
        
        # Construir query base
        base_filter = Q(example__project_id__in=project_ids)
        
        # Aplicar filtros comuns
        if user_ids:
            base_filter &= Q(user_id__in=user_ids)
        if example_ids:
            base_filter &= Q(example_id__in=example_ids)
        if date_from:
            base_filter &= Q(created_at__gte=date_from)
        if date_to:
            base_filter &= Q(created_at__lte=date_to)
        
        # Aplicar filtros de perspectiva
        if perspective_question_ids or perspective_answer_ids:
            # Filtrar utilizadores baseado nas perguntas/respostas da perspectiva
            from projects.models import Answer
            
            perspective_user_ids = set()
            
            if perspective_question_ids:
                # Obter utilizadores que responderam às perguntas especificadas
                question_user_ids = Answer.objects.filter(
                    question_id__in=perspective_question_ids
                ).values_list('member__user_id', flat=True).distinct()
                perspective_user_ids.update(question_user_ids)
            
            if perspective_answer_ids:
                # Obter utilizadores que deram as respostas especificadas
                answer_user_ids = Answer.objects.filter(
                    id__in=perspective_answer_ids
                ).values_list('member__user_id', flat=True).distinct()
                perspective_user_ids.update(answer_user_ids)
            
            if perspective_user_ids:
                base_filter &= Q(user_id__in=list(perspective_user_ids))
            else:
                # Se não há utilizadores que atendem aos critérios, retornar resultado vazio
                return {
                    'summary': {
                        'total_annotations': 0,
                        'total_examples': 0,
                        'total_annotators': 0,
                        'date_range_from': date_from,
                        'date_range_to': date_to,
                        'annotation_type_counts': {}
                    },
                    'data': [],
                    'total_pages': 0,
                    'current_page': page,
                    'page_size': page_size
                }
        
        all_annotations = []
        type_counts = defaultdict(int)
        
        # Para cada tipo de anotação
        for anno_type in valid_types:
            model_class = AnnotationReportService.ANNOTATION_TYPES[anno_type]
            
            # Construir filtro específico para o tipo
            type_filter = Q()
            if label_ids:
                if anno_type == 'category':
                    # Para categorias, filtrar por label_id diretamente
                    type_filter &= Q(label_id__in=label_ids)
                elif anno_type == 'span':
                    # Para spans, filtrar por label_id diretamente
                    type_filter &= Q(label_id__in=label_ids)
                elif anno_type == 'relation':
                    # Para relações, filtrar por type_id
                    type_filter &= Q(type_id__in=label_ids)
                    
            # Obter anotações para este tipo
            annotations = model_class.objects.filter(base_filter & type_filter)
            
            # Se não houver anotações, continuar para o próximo tipo
            if not annotations.exists():
                continue
                
            # Contar anotações deste tipo
            type_counts[anno_type] = annotations.count()
            
            # Aqui vamos usar select_related para otimizar as queries e apenas IDs para relações
            if anno_type == 'category':
                annotations = annotations.select_related('example', 'user', 'label')
            elif anno_type == 'span':
                annotations = annotations.select_related('example', 'user', 'label')
            elif anno_type == 'relation':
                annotations = annotations.select_related('example', 'user', 'type')
            else:  # text
                annotations = annotations.select_related('example', 'user')
            
            # Processar em blocos para reduzir uso de memória
            batch_size = 1000
            for i in range(0, annotations.count(), batch_size):
                for anno in annotations[i:i+batch_size]:
                    try:
                        # Obter detalhes específicos de acordo com o tipo de anotação
                        if anno_type == 'category':
                            label_id = anno.label_id if hasattr(anno, 'label_id') else None
                            label_text = anno.label.text if hasattr(anno, 'label') and anno.label else None
                            detail = None
                        elif anno_type == 'span':
                            label_id = anno.label_id if hasattr(anno, 'label_id') else None
                            label_text = anno.label.text if hasattr(anno, 'label') and anno.label else None
                            detail = {
                                'start_offset': anno.start_offset if hasattr(anno, 'start_offset') else None,
                                'end_offset': anno.end_offset if hasattr(anno, 'end_offset') else None,
                                'text': anno.text if hasattr(anno, 'text') else None
                            }
                        elif anno_type == 'relation':
                            label_id = anno.type_id if hasattr(anno, 'type_id') else None
                            label_text = anno.type.text if hasattr(anno, 'type') and anno.type else None
                            detail = {
                                'from_id': anno.from_id.id if hasattr(anno, 'from_id') and anno.from_id else None,
                                'to_id': anno.to_id.id if hasattr(anno, 'to_id') and anno.to_id else None
                            }
                        elif anno_type == 'text':
                            label_id = None
                            label_text = None
                            detail = {
                                'text': anno.text if hasattr(anno, 'text') else None
                            }
                        
                        # Obter informações do projeto - apenas o ID e nome
                        project_id = anno.example.project_id if hasattr(anno, 'example') and anno.example else None
                        project_name = ""
                        project_type = ""
                        if project_id:
                            try:
                                project = Project.objects.only('name', 'project_type').get(id=project_id)
                                project_name = project.name
                                project_type = project.project_type
                            except Project.DoesNotExist:
                                project_name = f"Projeto {project_id}"
                        
                        # Obter informações do exemplo - segurança para evitar acesso a arquivos
                        example_id = anno.example_id if hasattr(anno, 'example_id') else None
                        example_name = f"Exemplo {example_id}"
                        if hasattr(anno, 'example') and anno.example:
                            # Tentar usar o filename primeiro
                            if hasattr(anno.example, 'upload_name') and anno.example.upload_name:
                                example_name = str(anno.example.upload_name)
                            # Se não tiver filename, usar parte do texto
                            elif hasattr(anno.example, 'text') and anno.example.text:
                                text_content = str(anno.example.text)
                                example_name = text_content[:50] + ('...' if len(text_content) > 50 else '')
                        
                        # Obter informações do usuário - apenas string
                        user_id = anno.user_id if hasattr(anno, 'user_id') else None
                        username = "Desconhecido"
                        if hasattr(anno, 'user') and anno.user:
                            username = str(anno.user.username)
                        
                        # Garantir que timestamps sejam strings ISO
                        created_at = anno.created_at.isoformat() if hasattr(anno, 'created_at') and anno.created_at else None
                        updated_at = anno.updated_at.isoformat() if hasattr(anno, 'updated_at') and anno.updated_at else None
                        
                        # Criar item de anotação formatado - garantindo apenas tipos primitivos
                        annotation_item = {
                            'id': anno.id,
                            'type': anno_type,
                            'project_id': project_id,
                            'project_name': project_name,
                            'project_type': project_type,
                            'example_id': example_id,
                            'example_name': example_name,
                            'user_id': user_id,
                            'username': username,
                            'label_id': label_id,
                            'label_text': label_text,
                            'created_at': created_at,
                            'updated_at': updated_at,
                            'detail': detail
                        }
                        
                        all_annotations.append(annotation_item)
                    except Exception as e:
                        # Log erro sem interromper o processamento
                        print(f"Erro ao processar anotação {anno.id} do tipo {anno_type}: {str(e)}")
        
        # Aplicar filtro de discrepâncias se especificado
        if discrepancy_filter and discrepancy_filter != 'all':
            if discrepancy_filter == 'with_discrepancy':
                # Filtrar apenas anotações com discrepâncias
                # Por agora, este é um placeholder - a lógica de detecção de discrepâncias precisa ser implementada
                all_annotations = [anno for anno in all_annotations if AnnotationReportService._has_discrepancy(anno)]
            elif discrepancy_filter == 'without_discrepancy':
                # Filtrar apenas anotações sem discrepâncias
                all_annotations = [anno for anno in all_annotations if not AnnotationReportService._has_discrepancy(anno)]
        
        # Ordenar anotações por data de criação (mais recentes primeiro)
        all_annotations.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
        
        # Calcular paginação
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_annotations = all_annotations[start_idx:end_idx] if len(all_annotations) > start_idx else []
        
        # Calcular resumo geral
        # Usar valores já coletados em vez de fazer novas consultas
        unique_examples = set(a['example_id'] for a in all_annotations if a['example_id'])
        unique_users = set(a['user_id'] for a in all_annotations if a['user_id'])
        
        summary = {
            'total_annotations': len(all_annotations),
            'total_examples': len(unique_examples),
            'total_annotators': len(unique_users),
            'date_range_from': date_from.isoformat() if date_from else None,
            'date_range_to': date_to.isoformat() if date_to else None,
            'annotation_type_counts': dict(type_counts)
        }
        
        result = {
            'summary': summary,
            'data': paginated_annotations,
            'total_pages': (len(all_annotations) + page_size - 1) // page_size if page_size > 0 else 1,
            'current_page': page
        }
        
        return result
    
    @staticmethod
    def _has_discrepancy(annotation: Dict[str, Any]) -> bool:
        """
        Determina se uma anotação tem discrepâncias
        
        Por agora, esta é uma implementação placeholder.
        A lógica real de detecção de discrepâncias pode ser implementada aqui,
        por exemplo, verificando se múltiplos anotadores têm anotações diferentes
        para o mesmo exemplo ou posição.
        
        Args:
            annotation: Dicionário com dados da anotação
            
        Returns:
            True se a anotação tem discrepâncias, False caso contrário
        """
        # Implementação placeholder - pode ser expandida conforme necessário
        # Por exemplo, verificar se existem anotações conflitantes no mesmo exemplo
        
        # Por agora, retornar False para todas as anotações (sem discrepâncias)
        # Isso pode ser modificado para implementar lógica real de detecção
        return False 