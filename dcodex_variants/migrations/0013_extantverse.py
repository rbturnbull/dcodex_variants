# Generated by Django 3.1.3 on 2021-05-01 06:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dcodex", "0035_auto_20210216_0331"),
        ("dcodex_variants", "0012_remove_contra_family_witness"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExtantVerse",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "verse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="dcodex.verse"
                    ),
                ),
                (
                    "witness",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dcodex_variants.witnessbase",
                    ),
                ),
            ],
        ),
    ]