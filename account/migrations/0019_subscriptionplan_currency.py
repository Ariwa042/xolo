# Generated by Django 4.2 on 2025-05-07 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_rename_crypto_payment_cryptocurrency_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='currency',
            field=models.CharField(choices=[('USDT', 'USDT'), ('NGN', '₦')], default='USDT', max_length=4),
        ),
    ]
