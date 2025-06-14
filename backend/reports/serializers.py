from rest_framework import serializers
from django.contrib.auth.models import User
from projects.models import Project, Perspective
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
    perspective_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Lista de IDs das perspectivas (vazio = todas)"
    )
    dataset_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Lista de nomes dos datasets (vazio = todos)"
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

    def validate_perspective_ids(self, value):
        """Validar se as perspectivas existem"""
        if value:
            existing_perspectives = Perspective.objects.filter(id__in=value).count()
            if existing_perspectives != len(value):
                raise serializers.ValidationError("Algumas perspectivas especificadas não existem")
        
        return value


class AnnotatorReportResultSerializer(serializers.Serializer):
    """Serializer para resultados do relatório de anotadores"""
    annotator_id = serializers.IntegerField()
    annotator_name = serializers.CharField()
    annotator_username = serializers.CharField()
    label_breakdown = serializers.DictField(child=serializers.IntegerField())
    dataset_label_breakdown = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField()),
        required=False
    )


class AnnotatorReportSummarySerializer(serializers.Serializer):
    """Serializer para resumo do relatório de anotadores"""
    total_annotators = serializers.IntegerField()
    date_range_from = serializers.DateTimeField(allow_null=True)
    date_range_to = serializers.DateTimeField(allow_null=True)


class AnnotatorReportResponseSerializer(serializers.Serializer):
    """Serializer para resposta completa do relatório de anotadores"""
    summary = AnnotatorReportSummarySerializer()
    data = AnnotatorReportResultSerializer(many=True)


# Novos serializers para relatório de anotações

class AnnotationReportFilterSerializer(serializers.Serializer):
    """Serializer para filtros do relatório de anotações"""
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
    example_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Lista de IDs dos exemplos (vazio = todos)"
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
    annotation_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Lista de tipos de anotação (category, span, etc)"
    )

    def validate_project_ids(self, value):
        """Validar se os projetos existem"""
        if not value:
            raise serializers.ValidationError("Pelo menos um projeto deve ser especificado")
        
        existing_projects = Project.objects.filter(id__in=value).count()
        if existing_projects != len(value):
            raise serializers.ValidationError("Alguns projetos especificados não existem")
        
        return value


class AnnotationItemSerializer(serializers.Serializer):
    """Serializer para item individual de anotação"""
    id = serializers.IntegerField()
    type = serializers.CharField()  # category, span, relation, etc
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    example_id = serializers.IntegerField()
    example_name = serializers.CharField(allow_null=True, allow_blank=True)
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    label_id = serializers.IntegerField(allow_null=True)
    label_text = serializers.CharField(allow_null=True, allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    detail = serializers.JSONField(allow_null=True)  # Para campos específicos de cada tipo


class AnnotationReportSummarySerializer(serializers.Serializer):
    """Serializer para resumo do relatório de anotações"""
    total_annotations = serializers.IntegerField()
    total_examples = serializers.IntegerField()
    total_annotators = serializers.IntegerField()
    date_range_from = serializers.DateTimeField(allow_null=True)
    date_range_to = serializers.DateTimeField(allow_null=True)
    annotation_type_counts = serializers.DictField(child=serializers.IntegerField())


class AnnotationReportResponseSerializer(serializers.Serializer):
    """Serializer para resposta completa do relatório de anotações"""
    summary = AnnotationReportSummarySerializer()
    data = AnnotationItemSerializer(many=True) 