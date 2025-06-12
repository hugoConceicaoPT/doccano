# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_remove_votingcofiguration_example'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='answer_type',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ] 