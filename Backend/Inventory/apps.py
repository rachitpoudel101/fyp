from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Inventory'
    
    def ready(self):
        import Inventory.signals  # Import the signals
