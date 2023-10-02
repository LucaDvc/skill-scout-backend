# Generated by Django 4.2 on 2023-09-29 05:56

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeChallengeSubmission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('submitted_code', models.TextField(blank=True, null=True)),
                ('passed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('completed', models.BooleanField(default=False)),
                ('favourite', models.BooleanField(default=False)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, max_length=55, null=True)),
                ('compile_err', models.TextField(blank=True, null=True)),
                ('stderr', models.TextField(blank=True, null=True)),
                ('stdout', models.TextField(blank=True, null=True)),
                ('passed', models.BooleanField(default=False)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='learning.codechallengesubmission')),
                ('test_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.codechallengetestcase')),
            ],
        ),
        migrations.CreateModel(
            name='LearnerProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_chapters', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), blank=True, default=list, size=None)),
                ('completed_lessons', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), blank=True, default=list, size=None)),
                ('completed_steps', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), blank=True, default=list, size=None)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
                ('last_stopped_chapter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.chapter')),
                ('last_stopped_lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.lesson')),
                ('last_stopped_step', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.baselessonstep')),
            ],
        ),
    ]
