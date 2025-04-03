from django.db import models
from django.contrib.auth.models import User  # Using Django's built-in User model

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='documents/', null=True, blank=True)
    region = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.title} - {self.category}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.quantity * self.document.price  # Compute total price per item

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
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    ordered_at = models.DateTimeField(auto_now_add=True)

    def calculate_total_price(self):
        """Recalculate total order price based on OrderItems."""
        self.total_price = sum(item.total_price() for item in self.order_items.all())
        self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # Stores document price at purchase time

    def total_price(self):
        return self.quantity * self.price_at_purchase  # Compute total price of this item

    def __str__(self):
        return f"OrderItem {self.id} - {self.document.title} ({self.quantity} x {self.price_at_purchase})"


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
        ],
        default='unpaid'
    )

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.order.user.username} ({self.status})"

    def mark_as_paid(self):
        """Mark the invoice as paid and update order status."""
        self.status = 'paid'
        self.order.status = 'completed'
        self.order.save()
        self.save()
