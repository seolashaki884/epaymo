from django.db import models
from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal, ROUND_UP
import re
from datetime import timedelta

class Equipment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='equipments/', null=True, blank=True)
    rental_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # rate per hour
    status = models.CharField(max_length=50, choices=[
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


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
    no_of_days_hours = models.CharField(max_length=100, help_text="e.g., '2 days', '5 hours', '1.5 hours'")
    total_rent_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def parse_duration_in_hours(self):
        """
        Parses the `no_of_days_hours` string to a float representing total hours.
        Supported formats:
          - '2 days'
          - '5 hours'
          - '1.5 hours'
          - '2 days 3 hours'
        """
        text = self.no_of_days_hours.lower()
        days = re.search(r'(\d+(?:\.\d+)?)\s*day', text)
        hours = re.search(r'(\d+(?:\.\d+)?)\s*hour', text)

        total_hours = 0
        if days:
            total_hours += float(days.group(1)) * 24
        if hours:
            total_hours += float(hours.group(1))
        return round(total_hours, 2)

    def save(self, *args, **kwargs):
        if self.equipment and self.no_of_days_hours:
            total_hours = self.parse_duration_in_hours()
            rate = self.equipment.rental_rate
            cost = Decimal(rate) * Decimal(total_hours)
            # Optionally round up to the nearest cent
            self.total_rent_cost = cost.quantize(Decimal('0.01'), rounding=ROUND_UP)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requested_by} - {self.equipment.name} ({self.status})"

