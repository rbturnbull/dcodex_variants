# Generated by Django 3.0.6 on 2020-08-14 23:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dcodex", "0025_auto_20200809_1536"),
        ("dcodex_variants", "0010_contrarymanuscript"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ContraryManuscript",
            new_name="Contra",
        ),
    ]
