# Generated by Django 5.1.7 on 2025-03-22 22:28

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0004_tag_post_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrimeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='post',
            name='body',
        ),
        migrations.AddField(
            model_name='post',
            name='description',
            field=models.TextField(default='No description provided'),
        ),
        migrations.AddField(
            model_name='post',
            name='evidence',
            field=models.FileField(blank=True, null=True, upload_to='uploads/evidence/'),
        ),
        migrations.AddField(
            model_name='post',
            name='identifiers',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='incident_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='post',
            name='incident_time',
            field=models.TimeField(default='00:00:00'),
        ),
        migrations.AddField(
            model_name='post',
            name='location_city',
            field=models.CharField(default='unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='post',
            name='location_country',
            field=models.CharField(default='unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='post',
            name='location_province',
            field=models.CharField(default='unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='post',
            name='crime_types',
            field=models.ManyToManyField(to='social.crimetype'),
        ),
    ]
