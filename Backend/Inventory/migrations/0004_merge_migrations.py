from django.db import migrations

class Migration(migrations.Migration):
    """
    Merge migration to resolve conflict between 0002_add_expires_to_category and 0003_product_warehouse
    """
    
    dependencies = [
        ('Inventory', '0002_add_expires_to_category'),
        ('Inventory', '0003_product_warehouse'),
    ]
    
    operations = [
        # No operations needed, just merging the migration history
    ]
