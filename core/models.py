from django.db import models
from django.contrib.auth.models import User  # If using Django's built-in User model

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('drainage_fee', 'Drainage Fee'),
        ('equipment_rental', 'Equipment Rental'),
        ('filling_fee_certification', 'Filling Fee/Certification'),
        ('inspection_fee', 'Inspection Fee'),
        ('irrigation_services_fee', 'Irrigation Services Fee'),
        ('scraped_fix_assets', 'Scraped Fix Assets'),
        ('verification_authentication', 'Verification and Authentication'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    qty = models.IntegerField(default=1)
    image = models.ImageField(upload_to='documents/', null=True, blank=True)

    def __str__(self):
        return self.title

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    document_title = models.ForeignKey(Document, on_delete=models.CASCADE) 
    qty = models.PositiveIntegerField(default=1)  
    added_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.document.title} ({self.quantity})"

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    cart_items = models.ManyToManyField(Cart)  
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')  
    ordered_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"
