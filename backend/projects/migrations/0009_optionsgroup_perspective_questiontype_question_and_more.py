# Generated by Django 4.2.15 on 2025-03-27 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0008_project_allow_member_to_create_label_type_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OptionsGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="Perspective",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="projects.project")),
            ],
        ),
        migrations.CreateModel(
            name="QuestionType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_type", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                (
                    "options_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="options_group",
                        to="projects.optionsgroup",
                    ),
                ),
                (
                    "perspective",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="projects.perspective"
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="type", to="projects.questiontype"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OptionQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("option", models.TextField()),
                (
                    "options_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="option_questions",
                        to="projects.optionsgroup",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer_text", models.TextField()),
                (
                    "answer_option",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answer_option",
                        to="projects.optionquestion",
                    ),
                ),
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
