# Generated by Django 5.0.4 on 2024-08-15 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('1', 'CareerJudge Admin'), ('2', 'Corporate Admin'), ('3', 'Corporate Exclusive'), ('4', 'Psychometrician'), ('5', 'SME'), ('6', 'Reviewer'), ('7', 'Trainer'), ('8', 'Group Admin'), ('9', 'Counsellor'), ('10', 'Individual'), ('11', 'Channel Partner'), ('12', 'Corporate Individual'), ('13', 'CJ Manager'), ('14', 'Helpdesk')], default='9', max_length=10, verbose_name='User Role'),
        ),
    ]