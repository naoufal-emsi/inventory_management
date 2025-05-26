from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('SrockMaster', '0002_customer_purchase'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='contact',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='phone',
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
    ]
