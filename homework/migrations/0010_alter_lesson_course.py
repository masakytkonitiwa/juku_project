# Generated by Django 4.2.20 on 2025-04-26 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0009_eventtemplate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='course',
            field=models.CharField(choices=[('master', 'マスターコース'), ('top_level', '最高レベル特訓'), ('second', '2nd')], max_length=20),
        ),
    ]
