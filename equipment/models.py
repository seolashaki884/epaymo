from django.db import models
from django.contrib.auth.models import User

class Equipment(models.Model):
    name = models.CharField(max_length=255)
    asset_tag = models.CharField(max_length=50, unique=True) # Unique asset code/tag
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='equipments/', null=True, blank=True)
    rental_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rental_price = models.IntegerField()
    status = models.CharField(max_length=50, choices=[
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.asset_tag})"

class RentalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]

    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('billed', 'Billed'),
        ('paid', 'Paid'),
        ('waived', 'Waived'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='rental_requests')
    requested_by = models.CharField(max_length=255)
    purpose = models.TextField()
    rental_start_date = models.DateField()
    rental_end_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    no_of_days_hours = models.CharField(max_length=100)
    rental_rate = models.IntegerField()
    total_rent_cost = models.IntegerField(default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.total_rental_fee and self.rental_start_date and self.rental_end_date:
            duration = (self.rental_end_date - self.rental_start_date).days + 1
            self.total_rental_fee = self.rental_fee_per_day * duration
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requested_by} - {self.equipment.name} ({self.status})"
