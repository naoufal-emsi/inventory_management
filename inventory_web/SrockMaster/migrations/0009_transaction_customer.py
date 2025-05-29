from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('SrockMaster', '0008_customuser_balance_transaction_from_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='SrockMaster.customer'),
        ),
    ]
