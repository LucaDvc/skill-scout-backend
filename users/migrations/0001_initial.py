# Generated by Django 4.2 on 2023-11-17 10:53

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('learning', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('email', models.EmailField(db_index=True, error_messages={'unique': 'A user with that email already exists.'}, max_length=255, unique=True)),
                ('email_confirmed', models.BooleanField(default=False)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('city', models.CharField(blank=True, max_length=255, null=True)),
                ('short_bio', models.CharField(blank=True, max_length=255, null=True)),
                ('about', models.TextField(blank=True, null=True)),
                ('is_private', models.BooleanField(default=False)),
                ('picture', models.ImageField(blank=True, null=True, upload_to='')),
                ('linked_in', models.CharField(blank=True, max_length=200, null=True)),
                ('facebook', models.CharField(blank=True, max_length=200, null=True)),
                ('personal_website', models.CharField(blank=True, max_length=200, null=True)),
                ('youtube', models.CharField(blank=True, max_length=200, null=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('enrolled_courses', models.ManyToManyField(related_name='learners_enrolled', through='learning.CourseEnrollment', to='courses.course')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('wishlist', models.ManyToManyField(blank=True, related_name='wishlisted_by', to='courses.course')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
    ]
