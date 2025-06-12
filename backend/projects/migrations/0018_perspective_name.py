# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0017_alter_question_answer_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="perspective",
            name="name",
            field=models.CharField(default="Untitled Perspective", max_length=200),
            preserve_default=False,
        ),
    ] 