from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0001_initial'),  # Replace with your actual last migration
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='expires',
            field=models.BooleanField(default=False, help_text='Whether products in this category expire'),
        ),
    ]
