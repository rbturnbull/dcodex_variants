# Generated by Django 3.0.8 on 2020-08-09 02:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dcodex_variants', '0008_auto_20200808_1628'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='locationbase',
            options={'ordering': ['collection', 'rank']},
        ),
    ]
