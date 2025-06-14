# Generated manually for DatasetReview model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("examples", "0008_assignment"),
        ("labels", "0017_manualdiscrepancy"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatasetReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_approved", models.BooleanField(help_text="Whether the dataset is approved (True) or has discrepancies (False)")),
                ("comment", models.TextField(blank=True, help_text="Optional comment about the discrepancy")),
                ("label_agreements", models.JSONField(default=list, help_text="Label agreement details")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "example",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dataset_reviews",
                        to="examples.example",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dataset_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="datasetreview",
            unique_together={("example", "user")},
        ),
    ] 