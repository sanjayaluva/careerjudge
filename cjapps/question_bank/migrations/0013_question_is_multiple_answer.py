# Generated by Django 5.0.4 on 2024-08-21 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('question_bank', '0012_alter_question_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_multiple_answer',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
