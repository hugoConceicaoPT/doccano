from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_superuser",
            "is_staff",
        )
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "is_superuser": {"read_only": True},
            "is_staff": {"read_only": True},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # Garante que a senha será criptografada

        instance.save()
        return instance
