# Generated by Django 4.2.20 on 2025-04-22 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0003_event'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homework',
            name='estimated_minutes',
        ),
        migrations.RemoveField(
            model_name='homework',
            name='title',
        ),
        migrations.CreateModel(
            name='HomeworkDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.CharField(choices=[('master', 'マスターコース'), ('top_level', '最高レベル特訓')], max_length=20)),
                ('problem_type', models.CharField(choices=[('practice', '練習問題'), ('b_problem', 'B問題'), ('c_problem', 'C問題')], max_length=20)),
                ('problem_count', models.PositiveIntegerField()),
                ('homework', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='homework.homework')),
            ],
        ),
    ]
