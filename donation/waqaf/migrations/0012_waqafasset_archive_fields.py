# Generated manually for adding archive functionality to WaqafAsset

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('waqaf', '0011_waqafcart_waqafcartitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='waqafasset',
            name='is_archived',
            field=models.BooleanField(default=False, help_text='Archive this asset to hide it from public view'),
        ),
        migrations.AddField(
            model_name='waqafasset',
            name='archived_at',
            field=models.DateTimeField(blank=True, help_text='When this asset was archived', null=True),
        ),
        migrations.AddField(
            model_name='waqafasset',
            name='archived_by',
            field=models.ForeignKey(blank=True, help_text='User who archived this asset', null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user'),
        ),
    ]
