# Generated by Django 3.0.6 on 2020-08-14 23:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dcodex', '0025_auto_20200809_1536'),
        ('dcodex_variants', '0009_auto_20200809_1257'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContraryManuscript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attestation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_variants.Attestation')),
                ('family_witness', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex_variants.FamilyWitness')),
                ('manuscript', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex.Manuscript')),
                ('verse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dcodex.Verse')),
            ],
        ),
    ]
