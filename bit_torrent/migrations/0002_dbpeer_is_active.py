# Generated by Django 4.0.1 on 2022-01-28 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bit_torrent', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbpeer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]