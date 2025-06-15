from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from examples.models import Example
import pytz
from django.utils import timezone
from datetime import datetime

from .models import (
    Answer,
    BoundingBoxProject,
    ImageCaptioningProject,
    ImageClassificationProject,
    IntentDetectionAndSlotFillingProject,
    Member,
    Perspective,
    Project,
    Question,
    SegmentationProject,
    Seq2seqProject,
    SequenceLabelingProject,
    Speech2textProject,
    Tag,
    TextClassificationProject,
    AnnotationRule,
    VotingCofiguration,
    AnnotationRuleAnswers,
)


class MemberSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    rolename = serializers.SerializerMethodField()
    perspective_id = serializers.PrimaryKeyRelatedField(
        source="perspective", required=False, queryset=Perspective.objects.all(), allow_null=True
    )

    @classmethod
    def get_username(cls, instance):
        user = instance.user
        return user.username if user else None

    @classmethod
    def get_rolename(cls, instance):
        role = instance.role
        return role.name if role else None

    class Meta:
        model = Member
        fields = ("id", "user", "role", "username", "rolename", "perspective_id")




class AnswerSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    answer_text = serializers.CharField(required=True)

    class Meta:
        model = Answer
        fields = ("id", "member", "question", "answer_text")

    def validate(self, attrs):
        answer_text = attrs.get("answer_text", None)
        question = attrs.get("question", None)

        if not answer_text:
            raise serializers.ValidationError(
                "You must provide 'answer_text'."
            )

        # Validar baseado no tipo de pergunta, se especificado
        if question and question.answer_type:
            answer_type = question.answer_type
            
            if answer_type == 'boolean':
                if answer_text.lower() not in ['true', 'false']:
                    raise serializers.ValidationError(
                        "For boolean questions, answer must be 'true' or 'false'."
                    )
            elif answer_type == 'int':
                try:
                    int(answer_text)
                except ValueError:
                    raise serializers.ValidationError(
                        "For integer questions, answer must be a valid integer."
                    )
            elif answer_type == 'double':
                try:
                    float(answer_text)
                except ValueError:
                    raise serializers.ValidationError(
                        "For double questions, answer must be a valid number."
                    )
            # Para 'string' ou outros tipos, qualquer texto é válido

        return attrs


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    perspective = serializers.PrimaryKeyRelatedField(
        queryset=Perspective.objects.all(), required=False
    )
    answer_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Question
        fields = ("id", "question", "perspective", "answers", "answer_type")


class PerspectiveSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=Member.objects.filter(role__name="annotator"), many=True, required=False)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source="project",
    )
    questions = QuestionSerializer(many=True, read_only=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = Perspective
        fields = ("id", "name", "project_id", "created_at", "members", "questions")
        read_only_fields = ("created_at",)
    
    def validate_name(self, value):
        """
        Remover qualquer validação de unicidade para o nome da perspectiva
        """
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "project",
            "text",
        )
        read_only_fields = ("id", "project")


class AnswerNestedSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()

    class Meta:
        model = Answer
        fields = ("id", "answer", "member")


class QuestionNestedSerializer(serializers.ModelSerializer):
    answers = AnswerNestedSerializer(many=True, read_only=True, source="answers")

    class Meta:
        model = Question
        fields = ("id", "question", "answers")


class PerspectiveNestedSerializer(serializers.ModelSerializer):
    questions = QuestionNestedSerializer(many=True, read_only=True, source="questions")

    class Meta:
        model = Perspective
        fields = ("id", "name", "created_at", "questions")


class ProjectSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    author = serializers.SerializerMethodField()
    perspectives = PerspectiveNestedSerializer(many=True, read_only=True)

    @classmethod
    def get_author(cls, instance):
        if instance.created_by:
            return instance.created_by.username
        return ""

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "minPercentage",
            "description",
            "guideline",
            "project_type",
            "created_at",
            "updated_at",
            "random_order",
            "author",
            "collaborative_annotation",
            "single_class_classification",
            "allow_member_to_create_label_type",
            "is_text_project",
            "tags",
            "perspectives",
        ]
        read_only_fields = (
            "created_at",
            "updated_at",
            "author",
            "is_text_project",
        )

    def create(self, validated_data):
        tags = TagSerializer(data=validated_data.pop("tags", []), many=True)
        project = self.Meta.model.objects.create(**validated_data)
        tags.is_valid()
        tags.save(project=project)
        return project

    def update(self, instance, validated_data):
        # Don't update tags. Please use TagAPI.
        validated_data.pop("tags", None)
        return super().update(instance, validated_data)


class TextClassificationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = TextClassificationProject


class SequenceLabelingProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = SequenceLabelingProject
        fields = ProjectSerializer.Meta.fields + ["allow_overlapping", "grapheme_mode", "use_relation"]


class Seq2seqProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = Seq2seqProject


class IntentDetectionAndSlotFillingProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = IntentDetectionAndSlotFillingProject


class Speech2textProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = Speech2textProject


class ImageClassificationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = ImageClassificationProject


class BoundingBoxProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = BoundingBoxProject


class SegmentationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = SegmentationProject


class ImageCaptioningProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = ImageCaptioningProject


class ProjectPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        Project: ProjectSerializer,
        **{cls.Meta.model: cls for cls in ProjectSerializer.__subclasses__()},
    }

class PerspectiveListSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source="project"
    )
    project_name = serializers.CharField(source="project.name", read_only=True)
    creator_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Perspective
        fields = ("id", "name", "project_id", "project_name", "creator_name", "created_at")


class AnnotationRuleSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    voting_configuration = serializers.PrimaryKeyRelatedField(queryset=VotingCofiguration.objects.all())

    class Meta:
        model = AnnotationRule
        fields = [
            "id",
            "project",
            "name",
            "voting_configuration",
            "is_finalized",
            "final_result",
        ]

class VotingCofigurationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    created_by = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), allow_null=True)

    class Meta:
        model = VotingCofiguration
        fields = ['id', 'project', 'voting_threshold', 'percentage_threshold', 'created_by', 'begin_date', 'end_date', 'is_closed', 'version']

    def validate(self, attrs):
        # Simplesmente subtrair 1 hora das datas antes de salvar na base de dados
        from datetime import timedelta
        
        if 'begin_date' in attrs and attrs['begin_date']:
            if isinstance(attrs['begin_date'], str):
                # Se for string, converter para datetime primeiro
                try:
                    attrs['begin_date'] = datetime.fromisoformat(attrs['begin_date'])
                except ValueError:
                    # Tentar outros formatos se necessário
                    attrs['begin_date'] = datetime.strptime(attrs['begin_date'], '%Y-%m-%dT%H:%M')
            
            # Subtrair 1 hora
            attrs['begin_date'] = attrs['begin_date'] - timedelta(hours=1)
        
        if 'end_date' in attrs and attrs['end_date']:
            if isinstance(attrs['end_date'], str):
                # Se for string, converter para datetime primeiro
                try:
                    attrs['end_date'] = datetime.fromisoformat(attrs['end_date'])
                except ValueError:
                    # Tentar outros formatos se necessário
                    attrs['end_date'] = datetime.strptime(attrs['end_date'], '%Y-%m-%dT%H:%M')
            
            # Subtrair 1 hora
            attrs['end_date'] = attrs['end_date'] - timedelta(hours=1)
        
        # Validar as regras de negócio
        instance = VotingCofiguration(**attrs)
        instance.clean()
        return attrs

class AnnotationRuleAnswersSerializer(serializers.ModelSerializer):
    annotation_rule = serializers.PrimaryKeyRelatedField(queryset=AnnotationRule.objects.all())
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())

    class Meta:
        model = AnnotationRuleAnswers
        fields = ['id', 'annotation_rule', 'member', 'answer']
