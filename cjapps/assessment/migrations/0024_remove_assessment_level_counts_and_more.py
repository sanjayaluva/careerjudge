# Generated by Django 5.0.4 on 2025-01-16 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0023_rename_student_assessmentsession_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assessment',
            name='level_counts',
        ),
        migrations.AddField(
            model_name='section',
            name='delivery_count',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='timer_minutes',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
