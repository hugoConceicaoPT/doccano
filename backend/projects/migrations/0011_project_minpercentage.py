# Generated by Django 4.2.15 on 2025-04-02 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0010_alter_questiontype_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="minPercentage",
            field=models.IntegerField(default=0),
        ),
    ]
