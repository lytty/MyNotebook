# Generated by Django 2.0.7 on 2018-10-16 11:11

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('article', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ArticalColumn',
            new_name='ArticleColumn',
        ),
    ]
