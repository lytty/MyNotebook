# Generated by Django 2.1.2 on 2018-11-07 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0002_auto_20181108_0019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='url',
            field=models.URLField(max_length=600),
        ),
    ]