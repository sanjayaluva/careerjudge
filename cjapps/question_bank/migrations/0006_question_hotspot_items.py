# Generated by Django 5.0.4 on 2024-08-20 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('question_bank', '0005_rename_objective_question_objectives'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='hotspot_items',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
