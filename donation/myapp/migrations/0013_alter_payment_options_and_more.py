# Generated by Django 5.1.7 on 2025-06-09 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_alter_payment_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payment',
            options={},
        ),
        migrations.RemoveField(
            model_name='payment',
            name='_encrypted_bank_account',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='_encrypted_card_number',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='_encrypted_transaction_id',
        ),
        migrations.AddField(
            model_name='donation',
            name='message',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
        migrations.DeleteModel(
            name='AuditLog',
        ),
    ]
