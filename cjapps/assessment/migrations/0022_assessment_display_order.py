# Generated by Django 5.0.4 on 2024-10-27 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0021_assessment_duration_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='display_order',
            field=models.CharField(choices=[('sequential', 'Sequential'), ('random', 'Random')], default='random', max_length=10),
        ),
    ]