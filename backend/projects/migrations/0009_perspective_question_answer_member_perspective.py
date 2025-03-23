# Generated by Django 4.2.15 on 2025-03-22 20:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0008_project_allow_member_to_create_label_type_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Perspective",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="projects.project")),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                (
                    "perspective",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="projects.perspective"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer", models.TextField()),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="projects.member")),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="projects.question"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="member",
            name="perspective",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="members",
                to="projects.perspective",
            ),
        ),
    ]
