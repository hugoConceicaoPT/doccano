from rest_framework import serializers

from perspectives.models import Perspective
from projects.models import Member

class PerspectiveSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())

    class Meta:
        model = Perspective
        fields = (
            "id",
            "created_at",
            "updated_at",
            "questions",
            "answers",
            "member",
        )
        read_only_fields = ("member",)