# Generated by Django 5.0.4 on 2024-09-18 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0018_section_right_score_section_wrong_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='display_interval',
            field=models.PositiveIntegerField(default=0),
        ),
    ]