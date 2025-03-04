# Generated by Django 5.0.4 on 2024-08-23 15:18

import django_quill.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('question_bank', '0018_alter_question_is_multiple_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='instructions',
            field=django_quill.fields.QuillField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='objectives',
            field=django_quill.fields.QuillField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='paragraph',
            field=django_quill.fields.QuillField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=django_quill.fields.QuillField(blank=True, null=True),
        ),
    ]
