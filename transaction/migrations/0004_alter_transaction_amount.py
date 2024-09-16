# Generated by Django 5.1.1 on 2024-09-15 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transaction", "0003_transaction_terms_hash"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="amount",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
