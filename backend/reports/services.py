from typing import Dict, List, Optional, Any
from django.db.models import Count, Q, Min, Max, Avg, Case, When, IntegerField
from django.contrib.auth.models import User
from django.utils import timezone
from collections import defaultdict

from labels.models import Category, Span, TextLabel, Relation
from projects.models import Project, Member, Question, Answer
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
        dataset_names: Optional[List[str]] = None,
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None
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
            dataset_names: Lista de nomes dos datasets (opcional)
            perspective_question_ids: Lista de IDs das perguntas da perspectiva (opcional)
            perspective_answer_ids: Lista de IDs das respostas da perspectiva (opcional)
            
        Returns:
            Dicionário com summary e data do relatório
        """
        
        # Obter dados agregados por utilizador
        annotator_data = AnnotatorReportService._get_annotator_data(
            project_ids, user_ids, date_from, date_to, label_ids, perspective_ids, dataset_names, perspective_question_ids, perspective_answer_ids
        )
        
        # Calcular breakdown de rótulos para cada anotador
        for annotator in annotator_data:
            annotator['label_breakdown'] = AnnotatorReportService._get_label_breakdown(
                annotator['annotator_id'], project_ids, date_from, date_to, label_ids, perspective_ids, dataset_names, perspective_question_ids, perspective_answer_ids
            )
            # Adicionar informação detalhada sobre labels por dataset
            annotator['dataset_label_breakdown'] = AnnotatorReportService._get_dataset_label_breakdown(
                annotator['annotator_id'], project_ids, date_from, date_to, label_ids, perspective_ids, dataset_names, perspective_question_ids, perspective_answer_ids
            )
            # Adicionar informações sobre perguntas e respostas das perspectivas
            annotator['perspective_questions_answers'] = AnnotatorReportService._get_perspective_questions_answers(
                annotator['annotator_id'], project_ids, perspective_question_ids, perspective_answer_ids
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
        dataset_names: Optional[List[str]] = None,
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None
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
        
        # Filtrar apenas anotadores (excluir admins)
        from django.conf import settings
        annotator_user_ids = Member.objects.filter(
            project_id__in=project_ids,
            role__name=settings.ROLE_ANNOTATOR
        ).values_list('user_id', flat=True).distinct()
        
        if annotator_user_ids:
            base_filter &= Q(user_id__in=annotator_user_ids)
        
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
        
        # Aplicar filtro de perguntas da perspectiva
        if perspective_question_ids:
            print(f"[DEBUG] Aplicando filtro de perguntas: {perspective_question_ids}")
            print(f"[DEBUG] Project IDs: {project_ids}")
            
            # Debug: verificar se existem respostas para essas perguntas
            from projects.models import Answer
            answers_for_questions = Answer.objects.filter(question_id__in=perspective_question_ids)
            print(f"[DEBUG] Total de respostas para essas perguntas: {answers_for_questions.count()}")
            
            if answers_for_questions.exists():
                for answer in answers_for_questions[:3]:  # Mostrar apenas as primeiras 3
                    print(f"[DEBUG] Resposta: ID={answer.id}, Member={answer.member_id}, Question={answer.question_id}, Text='{answer.answer_text}'")
            
            # Obter IDs dos utilizadores que responderam às perguntas especificadas
            question_user_ids = Member.objects.filter(
                project_id__in=project_ids,
                answer__question_id__in=perspective_question_ids
            ).values_list('user_id', flat=True).distinct()
            
            print(f"[DEBUG] Utilizadores que responderam às perguntas: {list(question_user_ids)}")
            
            # Debug: verificar a query SQL
            query = Member.objects.filter(
                project_id__in=project_ids,
                answer__question_id__in=perspective_question_ids
            )
            print(f"[DEBUG] SQL Query: {query.query}")
            
            if question_user_ids:
                base_filter &= Q(user_id__in=question_user_ids)
                print(f"[DEBUG] Filtro aplicado com {len(question_user_ids)} utilizadores")
            else:
                # Se não há utilizadores que responderam às perguntas especificadas, retornar vazio
                print(f"[DEBUG] Nenhum utilizador encontrado para as perguntas especificadas")
                return []
        
        # Aplicar filtro de respostas da perspectiva
        if perspective_answer_ids:
            print(f"[DEBUG] Aplicando filtro de respostas: {perspective_answer_ids}")
            # Obter IDs dos utilizadores que deram as respostas especificadas
            answer_user_ids = Member.objects.filter(
                project_id__in=project_ids,
                answer__id__in=perspective_answer_ids
            ).values_list('user_id', flat=True).distinct()
            
            print(f"[DEBUG] Utilizadores que deram as respostas: {list(answer_user_ids)}")
            
            if answer_user_ids:
                base_filter &= Q(user_id__in=answer_user_ids)
                print(f"[DEBUG] Filtro aplicado com {len(answer_user_ids)} utilizadores")
            else:
                # Se não há utilizadores que deram as respostas especificadas, retornar vazio
                print(f"[DEBUG] Nenhum utilizador encontrado para as respostas especificadas")
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
            'annotator_name': '',
            'project_name': '',
            'project_id': None
        })
        
        # Obter informações dos projetos
        projects_info = {}
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                projects_info[project_id] = {
                    'name': project.name,
                    'id': project_id
                }
            except Project.DoesNotExist:
                projects_info[project_id] = {
                    'name': f"Projeto {project_id}",
                    'id': project_id
                }
        
        # Usar o primeiro projeto como referência para o nome do projeto
        first_project = list(projects_info.values())[0] if projects_info else {'name': 'N/A', 'id': None}
        
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
                'project_name': first_project['name'],
                'project_id': first_project['id']
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
        dataset_names: Optional[List[str]] = None,
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None
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
            
            # Aplicar filtro de perguntas da perspectiva
            if perspective_question_ids:
                # Obter os utilizadores que responderam às perguntas especificadas
                question_members = Member.objects.filter(
                    user_id=user_id,
                    project_id__in=project_ids,
                    answer__question_id__in=perspective_question_ids
                ).values_list('user_id', flat=True).distinct()
                
                if user_id not in question_members:
                    return {}
            
            # Aplicar filtro de respostas da perspectiva
            if perspective_answer_ids:
                # Obter os utilizadores que deram as respostas especificadas
                answer_members = Member.objects.filter(
                    user_id=user_id,
                    project_id__in=project_ids,
                    answer__id__in=perspective_answer_ids
                ).values_list('user_id', flat=True).distinct()
                
                if user_id not in answer_members:
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
        dataset_names: Optional[List[str]] = None,
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None
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
            
            # Aplicar filtro de perguntas da perspectiva
            if perspective_question_ids:
                # Obter os utilizadores que responderam às perguntas especificadas
                question_members = Member.objects.filter(
                    user_id=user_id,
                    project_id__in=project_ids,
                    answer__question_id__in=perspective_question_ids
                ).values_list('user_id', flat=True).distinct()
                
                if user_id not in question_members:
                    return {}
            
            # Aplicar filtro de respostas da perspectiva
            if perspective_answer_ids:
                # Obter os utilizadores que deram as respostas especificadas
                answer_members = Member.objects.filter(
                    user_id=user_id,
                    project_id__in=project_ids,
                    answer__id__in=perspective_answer_ids
                ).values_list('user_id', flat=True).distinct()
                
                if user_id not in answer_members:
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

    @staticmethod
    def _get_perspective_questions_answers(
        user_id: int,
        project_ids: List[int],
        perspective_question_ids: Optional[List[int]] = None,
        perspective_answer_ids: Optional[List[int]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obter perguntas e respostas das perspectivas para um utilizador"""
        
        try:
            result = {}
            
            # Construir filtro base
            filter_kwargs = {
                'member__user_id': user_id,
                'member__project_id__in': project_ids
            }
            
            # Aplicar filtro de perguntas se especificado
            if perspective_question_ids:
                filter_kwargs['question_id__in'] = perspective_question_ids
            
            # Aplicar filtro de respostas se especificado
            if perspective_answer_ids:
                filter_kwargs['id__in'] = perspective_answer_ids
            
            # Obter perguntas e respostas do utilizador com filtros aplicados
            user_answers = Answer.objects.filter(**filter_kwargs).select_related('question')
            
            print(f"[DEBUG] Filtros aplicados para utilizador {user_id}: {filter_kwargs}")
            print(f"[DEBUG] Respostas encontradas: {user_answers.count()}")
            
            if user_answers.exists():
                # Organizar perguntas únicas
                questions = {}
                answers_list = []
                
                for answer in user_answers:
                    # Adicionar pergunta
                    if answer.question_id not in questions:
                        questions[answer.question_id] = {
                            'question_id': answer.question_id,
                            'question_text': answer.question.question
                        }
                    
                    # Adicionar resposta
                    answer_text = answer.answer_text or (answer.answer_option.option if answer.answer_option else 'Sem resposta')
                    answers_list.append({
                        'answer_id': answer.id,
                        'answer_text': answer_text,
                        'question_id': answer.question_id,
                        'question_text': answer.question.question
                    })
                
                result['questions'] = list(questions.values())
                result['answers'] = answers_list
                
                print(f"[DEBUG] Perguntas retornadas: {len(result['questions'])}")
                print(f"[DEBUG] Respostas retornadas: {len(result['answers'])}")
            else:
                result['questions'] = []
                result['answers'] = []
                print(f"[DEBUG] Nenhuma resposta encontrada para utilizador {user_id}")
            
            return result
            
        except Exception as e:
            print(f"[DEBUG] Erro ao obter perguntas e respostas das perspectivas: {e}")
            import traceback
            traceback.print_exc()
            return {'questions': [], 'answers': []} 


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
        
        # Filtrar apenas anotadores (excluir admins)
        from django.conf import settings
        annotator_user_ids = Member.objects.filter(
            project_id__in=project_ids,
            role__name=settings.ROLE_ANNOTATOR
        ).values_list('user_id', flat=True).distinct()
        
        if annotator_user_ids:
            base_filter &= Q(user_id__in=annotator_user_ids)
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
            
            if perspective_question_ids and perspective_answer_ids:
                # Se ambos os filtros estão especificados, usar interseção (AND lógico)
                # Utilizadores que responderam às perguntas E deram as respostas específicas
                question_user_ids = set(Answer.objects.filter(
                    question_id__in=perspective_question_ids
                ).values_list('member__user_id', flat=True).distinct())
                
                answer_user_ids = set(Answer.objects.filter(
                    id__in=perspective_answer_ids
                ).values_list('member__user_id', flat=True).distinct())
                
                # Interseção: utilizadores que atendem a ambos os critérios
                perspective_user_ids = question_user_ids.intersection(answer_user_ids)
                
            elif perspective_question_ids:
                # Apenas filtro de perguntas: utilizadores que responderam às perguntas especificadas
                question_user_ids = Answer.objects.filter(
                    question_id__in=perspective_question_ids
                ).values_list('member__user_id', flat=True).distinct()
                perspective_user_ids.update(question_user_ids)
                
            elif perspective_answer_ids:
                # Apenas filtro de respostas: utilizadores que deram exatamente as respostas especificadas
                # Obter as respostas específicas para verificar as perguntas associadas
                specific_answers = Answer.objects.filter(
                    id__in=perspective_answer_ids
                ).select_related('question')
                
                # Agrupar por pergunta para verificar se o utilizador deu exatamente essas respostas
                question_to_answers = {}
                for answer in specific_answers:
                    question_id = answer.question_id
                    if question_id not in question_to_answers:
                        question_to_answers[question_id] = []
                    question_to_answers[question_id].append(answer.id)
                
                # Para cada pergunta, verificar quais utilizadores deram exatamente as respostas especificadas
                valid_user_ids = set()
                for question_id, expected_answer_ids in question_to_answers.items():
                    # Obter todos os utilizadores que responderam a esta pergunta
                    users_for_question = Answer.objects.filter(
                        question_id=question_id
                    ).values_list('member__user_id', flat=True).distinct()
                    
                    for user_id in users_for_question:
                        # Obter todas as respostas deste utilizador para esta pergunta
                        user_answer_ids = list(Answer.objects.filter(
                            question_id=question_id,
                            member__user_id=user_id
                        ).values_list('id', flat=True))
                        
                        # Verificar se as respostas do utilizador coincidem com as esperadas
                        if set(user_answer_ids).intersection(set(expected_answer_ids)):
                            valid_user_ids.add(user_id)
                            print(f"[DEBUG] Utilizador {user_id} tem resposta válida para pergunta {question_id}: {user_answer_ids} ∩ {expected_answer_ids}")
                
                perspective_user_ids.update(valid_user_ids)
            
            print(f"[DEBUG] Filtro de perspectiva aplicado:")
            print(f"[DEBUG] - Perguntas: {perspective_question_ids}")
            print(f"[DEBUG] - Respostas: {perspective_answer_ids}")
            print(f"[DEBUG] - Utilizadores encontrados: {list(perspective_user_ids)}")
            
            if perspective_user_ids:
                base_filter &= Q(user_id__in=list(perspective_user_ids))
            else:
                # Se não há utilizadores que atendem aos critérios, retornar resultado vazio
                print(f"[DEBUG] Nenhum utilizador encontrado para os critérios de perspectiva")
                return {
                    'summary': {
                        'total_annotations': 0,
                        'total_examples': 0,
                        'total_annotators': 0,
                        'date_range_from': date_from.isoformat() if date_from else None,
                        'date_range_to': date_to.isoformat() if date_to else None,
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
                                from projects.models import Project
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
            print(f"[DEBUG] Aplicando filtro de discrepâncias: {discrepancy_filter}")
            print(f"[DEBUG] Total de anotações antes do filtro: {len(all_annotations)}")
            
            # Verificar se há anotações para processar
            if not all_annotations:
                print(f"[DEBUG] Nenhuma anotação encontrada para aplicar filtro de discrepâncias")
            else:
                # Usar lógica simples baseada na contagem de utilizadores únicos por exemplo
                examples_with_discrepancy = AnnotationReportService._get_examples_with_discrepancy(all_annotations)
                print(f"[DEBUG] Exemplos com discrepância encontrados: {examples_with_discrepancy}")
                
                if discrepancy_filter == 'with_discrepancy':
                    # Filtrar apenas anotações de exemplos com discrepâncias
                    all_annotations = [anno for anno in all_annotations if anno.get('example_id') in examples_with_discrepancy]
                    print(f"[DEBUG] Anotações com discrepância encontradas: {len(all_annotations)}")
                elif discrepancy_filter == 'without_discrepancy':
                    # Filtrar apenas anotações de exemplos sem discrepâncias
                    all_annotations = [anno for anno in all_annotations if anno.get('example_id') not in examples_with_discrepancy]
                    print(f"[DEBUG] Anotações sem discrepância encontradas: {len(all_annotations)}")
        
        # Agrupar anotações por utilizador e exemplo para consolidar labels
        consolidated_annotations = AnnotationReportService._consolidate_annotations_by_user_example(all_annotations)
        
        # Ordenar anotações consolidadas por data de criação (mais recentes primeiro)
        consolidated_annotations.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
        
        # Calcular paginação
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_annotations = consolidated_annotations[start_idx:end_idx] if len(consolidated_annotations) > start_idx else []
        
        # Calcular resumo geral
        # Usar valores já coletados em vez de fazer novas consultas
        unique_examples = set(a['example_id'] for a in all_annotations if a['example_id'])
        unique_users = set(a['user_id'] for a in all_annotations if a['user_id'])
        
        summary = {
            'total_annotations': len(consolidated_annotations),  # Usar anotações consolidadas
            'total_examples': len(unique_examples),
            'total_annotators': len(unique_users),
            'date_range_from': date_from.isoformat() if date_from else None,
            'date_range_to': date_to.isoformat() if date_to else None,
            'annotation_type_counts': dict(type_counts)
        }
        
        result = {
            'summary': summary,
            'data': paginated_annotations,
            'total_pages': (len(consolidated_annotations) + page_size - 1) // page_size if page_size > 0 else 1,  # Usar anotações consolidadas
            'current_page': page
        }
        
        return result
    
    @staticmethod
    def _get_examples_with_discrepancy(all_annotations: List[Dict[str, Any]]) -> set:
        """
        Identifica exemplos que têm discrepâncias usando lógica simples.
        
        Um exemplo tem discrepância se:
        - Há múltiplos utilizadores que anotaram o mesmo exemplo
        - E esses utilizadores fizeram anotações diferentes (diferentes labels ou tipos)
        
        Args:
            all_annotations: Lista de todas as anotações
            
        Returns:
            Set com IDs dos exemplos que têm discrepâncias
        """
        examples_with_discrepancy = set()
        
        # Agrupar anotações por exemplo
        examples_annotations = {}
        for anno in all_annotations:
            example_id = anno.get('example_id')
            if example_id:
                if example_id not in examples_annotations:
                    examples_annotations[example_id] = []
                examples_annotations[example_id].append(anno)
        
        # Verificar cada exemplo
        for example_id, annotations in examples_annotations.items():
            # Obter utilizadores únicos neste exemplo
            users = set(anno.get('user_id') for anno in annotations if anno.get('user_id'))
            
            # Se há apenas um utilizador, não há discrepância
            if len(users) < 2:
                continue
            
            # Verificar se há anotações diferentes entre utilizadores
            has_discrepancy = False
            
            # Agrupar anotações por utilizador
            user_annotations = {}
            for anno in annotations:
                user_id = anno.get('user_id')
                if user_id:
                    if user_id not in user_annotations:
                        user_annotations[user_id] = []
                    user_annotations[user_id].append(anno)
            
            # Comparar anotações entre utilizadores
            user_signatures = {}
            for user_id, user_annos in user_annotations.items():
                # Criar uma "assinatura" das anotações do utilizador
                signature = set()
                for anno in user_annos:
                    anno_type = anno.get('type')
                    label_id = anno.get('label_id')
                    
                    # Para spans, incluir posições na assinatura
                    if anno_type == 'span':
                        detail = anno.get('detail', {})
                        start = detail.get('start_offset')
                        end = detail.get('end_offset')
                        signature.add((anno_type, label_id, start, end))
                    # Para outros tipos, usar apenas tipo e label
                    else:
                        signature.add((anno_type, label_id))
                
                user_signatures[user_id] = signature
            
            # Se há utilizadores com assinaturas diferentes, há discrepância
            signatures_list = list(user_signatures.values())
            if len(signatures_list) > 1:
                # Comparar todas as assinaturas entre si
                first_signature = signatures_list[0]
                for signature in signatures_list[1:]:
                    if signature != first_signature:
                        has_discrepancy = True
                        print(f"[DEBUG] Discrepância detectada no exemplo {example_id}: {first_signature} != {signature}")
                        break
            
            if has_discrepancy:
                examples_with_discrepancy.add(example_id)
                print(f"[DEBUG] Discrepância detectada no exemplo {example_id} com {len(users)} utilizadores")
        
        print(f"[DEBUG] Total de exemplos com discrepância: {len(examples_with_discrepancy)}")
        return examples_with_discrepancy
    
    @staticmethod
    def _consolidate_annotations_by_user_example(all_annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolida anotações agrupando por utilizador e exemplo.
        
        Em vez de ter uma linha por cada anotação individual, agrupa todas as anotações
        do mesmo utilizador no mesmo exemplo numa única linha, consolidando as labels.
        
        Args:
            all_annotations: Lista de todas as anotações individuais
            
        Returns:
            Lista de anotações consolidadas (uma por utilizador/exemplo)
        """
        consolidated = {}
        
        for anno in all_annotations:
            user_id = anno.get('user_id')
            example_id = anno.get('example_id')
            
            if not user_id or not example_id:
                continue
            
            # Criar chave única para utilizador + exemplo
            key = f"{user_id}_{example_id}"
            
            if key not in consolidated:
                # Primeira anotação deste utilizador neste exemplo
                consolidated[key] = {
                    'id': f"consolidated_{key}",  # ID único para a linha consolidada
                    'user_id': user_id,
                    'username': anno.get('username'),
                    'example_id': example_id,
                    'example_name': anno.get('example_name'),
                    'project_id': anno.get('project_id'),
                    'project_name': anno.get('project_name'),
                    'project_type': anno.get('project_type'),
                    'created_at': anno.get('created_at'),  # Usar a data da primeira anotação
                    'updated_at': anno.get('updated_at'),
                    'labels': [],  # Lista de todas as labels usadas
                    'annotation_types': set(),  # Tipos de anotação usados
                    'annotation_count': 0,  # Número total de anotações
                    'details': []  # Detalhes de todas as anotações
                }
            
            # Adicionar informações desta anotação à consolidação
            consolidated_item = consolidated[key]
            
            # Adicionar label se existir
            label_text = anno.get('label_text')
            if label_text:
                consolidated_item['labels'].append({
                    'text': label_text,
                    'type': anno.get('type'),
                    'id': anno.get('label_id')
                })
            
            # Adicionar tipo de anotação
            anno_type = anno.get('type')
            if anno_type:
                consolidated_item['annotation_types'].add(anno_type)
            
            # Incrementar contador
            consolidated_item['annotation_count'] += 1
            
            # Adicionar detalhes se existirem
            detail = anno.get('detail')
            if detail:
                consolidated_item['details'].append({
                    'type': anno_type,
                    'detail': detail
                })
            
            # Atualizar data se esta anotação for mais recente
            if anno.get('created_at') and (not consolidated_item['created_at'] or anno.get('created_at') > consolidated_item['created_at']):
                consolidated_item['created_at'] = anno.get('created_at')
                consolidated_item['updated_at'] = anno.get('updated_at')
        
        # Converter para lista e formatar campos finais
        result = []
        for consolidated_item in consolidated.values():
            # Converter set para lista
            consolidated_item['annotation_types'] = list(consolidated_item['annotation_types'])
            
            # Criar texto consolidado das labels
            if consolidated_item['labels']:
                # Agrupar labels por tipo
                labels_by_type = {}
                for label in consolidated_item['labels']:
                    label_type = label['type']
                    if label_type not in labels_by_type:
                        labels_by_type[label_type] = []
                    labels_by_type[label_type].append(label['text'])
                
                # Criar texto formatado
                label_parts = []
                for label_type, texts in labels_by_type.items():
                    unique_texts = list(set(texts))  # Remover duplicatas
                    label_parts.append(f"{label_type.title()}: {', '.join(unique_texts)}")
                
                consolidated_item['label_text'] = ' | '.join(label_parts)
            else:
                consolidated_item['label_text'] = 'Sem labels'
            
            # Criar campo de tipo consolidado
            if consolidated_item['annotation_types']:
                consolidated_item['type'] = ', '.join(consolidated_item['annotation_types'])
            else:
                consolidated_item['type'] = 'Desconhecido'
            
            result.append(consolidated_item)
        
        print(f"[DEBUG] Consolidação: {len(all_annotations)} anotações individuais → {len(result)} anotações consolidadas")
        return result 