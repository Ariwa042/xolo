# Generated by Django 4.2 on 2025-05-07 12:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_cryptocurrency_qr_code'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Cryptocurrency',
            new_name='Crypto_Payment',
        ),
        migrations.AlterModelOptions(
            name='crypto_payment',
            options={'verbose_name': 'Crypto Payment', 'verbose_name_plural': 'Crypto Payments'},
        ),
        migrations.RenameField(
            model_name='deposit',
            old_name='cryptocurrency',
            new_name='crypto_payment',
        ),
    ]
