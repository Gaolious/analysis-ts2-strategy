# Generated by Django 4.1.4 on 2023-01-28 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playerwhistleitem',
            name='article',
        ),
        migrations.AddField(
            model_name='playerwhistleitem',
            name='item_id',
            field=models.IntegerField(default=0, verbose_name='value'),
        ),
    ]
