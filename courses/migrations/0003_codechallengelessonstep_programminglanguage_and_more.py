# Generated by Django 4.2 on 2023-09-21 08:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeChallengeLessonStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('initial_code', models.TextField(blank=True, null=True)),
                ('proposed_solution', models.TextField(blank=True, null=True)),
                ('base_step', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='code_challenge_step', to='courses.baselessonstep')),
            ],
        ),
        migrations.CreateModel(
            name='ProgrammingLanguage',
            fields=[
                ('id', models.SmallIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='quizchoice',
            name='correct',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='videolessonstep',
            name='base_step',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='video_step', to='courses.baselessonstep'),
        ),
        migrations.CreateModel(
            name='CodeChallengeTestCase',
            fields=[
                ('id', models.SmallAutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('input', models.TextField()),
                ('expected_output', models.TextField()),
                ('code_challenge_step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_case', to='courses.codechallengelessonstep')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='codechallengelessonstep',
            name='language',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.programminglanguage'),
        ),
    ]
