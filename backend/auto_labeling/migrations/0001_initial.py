# Generated by Django 3.2.11 on 2022-01-20 04:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("api", "0030_delete_autolabelingconfig"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="AutoLabelingConfig",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                            ),
                        ),
                        ("model_name", models.CharField(max_length=100)),
                        ("model_attrs", models.JSONField(default=dict)),
                        ("template", models.TextField(default="")),
                        ("label_mapping", models.JSONField(blank=True, default=dict)),
                        ("default", models.BooleanField(default=False)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "project",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="auto_labeling_config",
                                to="api.project",
                            ),
                        ),
                    ],
                ),
            ],
            database_operations=[],
        )
    ]
