# Generated by Django 2.0.7 on 2018-10-20 09:30

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0004_auto_20181020_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlepost',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2018, 10, 20, 9, 30, 46, 830916, tzinfo=utc)),
        ),
    ]
