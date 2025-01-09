from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    stock = models.IntegerField()
    purchase_date = models.DateField()

    def __str__(self):
        return self.name

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_no = models.CharField(max_length=50)
    expiry_date = models.DateField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} - Batch {self.batch_no}"