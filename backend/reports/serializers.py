from rest_framework import serializers
from django.contrib.auth.models import User
from projects.models import Project
from label_types.models import CategoryType, SpanType


class AnnotatorReportFilterSerializer(serializers.Serializer):
    """Serializer para filtros do relatório de anotadores"""
    project_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="Lista de IDs dos projetos"
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Lista de IDs dos utilizadores (vazio = todos)"
    )
    date_from = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Data de início (formato ISO)"
    )
    date_to = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Data de fim (formato ISO)"
    )
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Lista de IDs dos rótulos (vazio = todos)"
    )
    task_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Lista de tipos de tarefa"
    )

    def validate_project_ids(self, value):
        """Validar se os projetos existem"""
        if not value:
            raise serializers.ValidationError("Pelo menos um projeto deve ser especificado")
        
        existing_projects = Project.objects.filter(id__in=value).count()
        if existing_projects != len(value):
            raise serializers.ValidationError("Alguns projetos especificados não existem")
        
        return value

    def validate_user_ids(self, value):
        """Validar se os utilizadores existem"""
        if value:
            existing_users = User.objects.filter(id__in=value).count()
            if existing_users != len(value):
                raise serializers.ValidationError("Alguns utilizadores especificados não existem")
        
        return value


class AnnotatorReportResultSerializer(serializers.Serializer):
    """Serializer para resultados do relatório de anotadores"""
    annotator_id = serializers.IntegerField()
    annotator_name = serializers.CharField()
    annotator_username = serializers.CharField()
    first_annotation_date = serializers.DateTimeField(allow_null=True)
    last_annotation_date = serializers.DateTimeField(allow_null=True)
    label_breakdown = serializers.DictField(child=serializers.IntegerField())


class AnnotatorReportSummarySerializer(serializers.Serializer):
    """Serializer para resumo do relatório de anotadores"""
    total_annotators = serializers.IntegerField()
    date_range_from = serializers.DateTimeField(allow_null=True)
    date_range_to = serializers.DateTimeField(allow_null=True)


class AnnotatorReportResponseSerializer(serializers.Serializer):
    """Serializer para resposta completa do relatório de anotadores"""
    summary = AnnotatorReportSummarySerializer()
    data = AnnotatorReportResultSerializer(many=True) 