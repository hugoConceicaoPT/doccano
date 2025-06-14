# Generated manually to remove options_group field from Question model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0021_alter_perspective_project"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="question",
            name="options_group",
        ),
    ] 