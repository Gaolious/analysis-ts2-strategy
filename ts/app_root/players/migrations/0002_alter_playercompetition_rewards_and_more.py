# Generated by Django 4.1.4 on 2023-04-04 10:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("players", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="playercompetition",
            name="rewards",
            field=models.CharField(default="", max_length=500, verbose_name="Rewards"),
        ),
        migrations.AlterField(
            model_name="playercontract",
            name="reward",
            field=models.CharField(default="", max_length=500, verbose_name="reward"),
        ),
        migrations.AlterField(
            model_name="playerdailyofferitem",
            name="reward",
            field=models.CharField(default="", max_length=500, verbose_name="reward"),
        ),
        migrations.AlterField(
            model_name="playerdailyreward",
            name="rewards",
            field=models.CharField(default="", max_length=500, verbose_name="Rewards"),
        ),
        migrations.AlterField(
            model_name="playergift",
            name="reward",
            field=models.CharField(default="", max_length=500, verbose_name="reward"),
        ),
        migrations.AlterField(
            model_name="playerjob",
            name="reward",
            field=models.CharField(default="", max_length=500, verbose_name="reward"),
        ),
        migrations.AlterField(
            model_name="playerleaderboardprogress",
            name="rewards",
            field=models.CharField(default="", max_length=500, verbose_name="rewards"),
        ),
        migrations.AlterField(
            model_name="playershipoffer",
            name="reward",
            field=models.CharField(default="", max_length=500, verbose_name="reward"),
        ),
    ]