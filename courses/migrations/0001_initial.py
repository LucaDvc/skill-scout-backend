# Generated by Django 4.2 on 2023-11-17 10:53

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseLessonStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('order', models.PositiveIntegerField(blank=True)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.SmallAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('title', models.CharField(max_length=100)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['creation_date'],
            },
        ),
        migrations.CreateModel(
            name='CodeChallengeTestCase',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('input', models.TextField(unique=True)),
                ('expected_output', models.TextField()),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('title', models.CharField(max_length=100)),
                ('intro', models.TextField(blank=True, max_length=300, null=True)),
                ('description', models.TextField(blank=True, null=True, validators=[django.core.validators.MinLengthValidator(100, 'the description must be at least 100 characters long')])),
                ('requirements', models.TextField(blank=True, null=True)),
                ('total_hours', models.DecimalField(blank=True, decimal_places=0, max_digits=3, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('release_date', models.DateField(blank=True, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=0, default=0, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('title', models.CharField(max_length=50)),
                ('order', models.PositiveIntegerField(blank=True)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ProgrammingLanguage',
            fields=[
                ('id', models.SmallIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='QuizChoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('text', models.CharField(max_length=100)),
                ('correct', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='CodeChallengeLessonStep',
            fields=[
                ('base_step', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='code_challenge_step', serialize=False, to='courses.baselessonstep')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('initial_code', models.TextField(blank=True, null=True)),
                ('proposed_solution', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='QuizLessonStep',
            fields=[
                ('base_step', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='quiz_step', serialize=False, to='courses.baselessonstep')),
                ('question', models.TextField(max_length=500)),
                ('explanation', models.TextField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TextLessonStep',
            fields=[
                ('base_step', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='text_step', serialize=False, to='courses.baselessonstep')),
                ('text', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VideoLessonStep',
            fields=[
                ('base_step', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='video_step', serialize=False, to='courses.baselessonstep')),
                ('title', models.CharField(blank=True, max_length=150, null=True)),
                ('video_file', models.FileField(blank=True, null=True, upload_to='', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True, max_length=500, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
            ],
        ),
    ]
