from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from examples.models import Example

from .models import (
    Answer,
    BoundingBoxProject,
    ImageCaptioningProject,
    ImageClassificationProject,
    IntentDetectionAndSlotFillingProject,
    Member,
    OptionQuestion,
    OptionsGroup,
    Perspective,
    Project,
    Question,
    SegmentationProject,
    Seq2seqProject,
    SequenceLabelingProject,
    Speech2textProject,
    Tag,
    TextClassificationProject,
    AnnotationRuleType,
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

class OptionQuestionSerializer(serializers.ModelSerializer):
    options_group = serializers.PrimaryKeyRelatedField(queryset=OptionsGroup.objects.all(), required=False)

    class Meta:
        model = OptionQuestion
        fields = ["id", "option", "options_group"]


class OptionsGroupSerializer(serializers.ModelSerializer):
    options_questions = OptionQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = OptionsGroup
        fields = ["id", "name", "options_questions"]


class AnswerSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    answer_option = serializers.PrimaryKeyRelatedField(queryset=OptionQuestion.objects.all(), required=False)
    answer_text = serializers.CharField(required=False)

    class Meta:
        model = Answer
        fields = ("id", "member", "question", "answer_text", "answer_option")

    def validate(self, attrs):
        answer_text = attrs.get("answer_text", None)
        answer_option = attrs.get("answer_option", None)

        if answer_text and answer_option:
            raise serializers.ValidationError(
                "You can only provide one of the fiels: 'answer_text' or 'answer_option', but not both."
            )

        if not answer_text and not answer_option:
            raise serializers.ValidationError(
                "You must provide at least one of the fields: 'answer_text' or 'answer_option'."
            )

        return attrs


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    perspective = serializers.PrimaryKeyRelatedField(
        queryset=Perspective.objects.all(), required=False
    )
    options_group = serializers.PrimaryKeyRelatedField(queryset=OptionsGroup.objects.all(), required=False)
    answer_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Question
        fields = ("id", "question", "perspective", "answers", "options_group", "answer_type")


class PerspectiveSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=Member.objects.filter(role__name="annotator"), many=True)
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


class AnnotationRuleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationRuleType
        fields = ['id', 'annotation_rule_type']

class AnnotationRuleSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    voting_configuration = serializers.PrimaryKeyRelatedField(queryset=VotingCofiguration.objects.all())
    annotation_rule_type = serializers.PrimaryKeyRelatedField(queryset=AnnotationRuleType.objects.all())

    class Meta:
        model = AnnotationRule
        fields = [
            "id",
            "project",
            "name",
            "description",
            "voting_configuration",
            "annotation_rule_type",
            "is_finalized",
            "final_result",
        ]

class VotingCofigurationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    annotation_rule_type = serializers.PrimaryKeyRelatedField(queryset=AnnotationRuleType.objects.all())
    created_by = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), allow_null=True)

    class Meta:
        model = VotingCofiguration
        fields = ['id', 'project', 'annotation_rule_type', 'voting_threshold', 'percentage_threshold', 'created_by', 'begin_date', 'end_date']

class AnnotationRuleAnswersSerializer(serializers.ModelSerializer):
    annotation_rule = serializers.PrimaryKeyRelatedField(queryset=AnnotationRule.objects.all())
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    annotation_rule_type = serializers.PrimaryKeyRelatedField(queryset=AnnotationRuleType.objects.all())

    class Meta:
        model = AnnotationRuleAnswers
        fields = ['id', 'annotation_rule', 'member', 'answer', 'annotation_rule_type']
