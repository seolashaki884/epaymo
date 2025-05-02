from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    CATEGORY_CHOICES = [
    ('drainage_fee', 'Drainage Fee'),
    ('equipment_rental', 'Equipment Rental'),
    ('filling_fee_certification', 'Filling Fee/Certification'),
    ('inspection_fee', 'Inspection Fee'),
    ('irrigation_services_fee', 'Irrigation Services Fee'),
    ('scraped_fix_assets', 'Scraped Fix Assets'),
    ('verification_authentication', 'Verification and Authentication'),
    ('bidding_documents', 'Bidding Documents'),

]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('drainage_fee', 'Drainage Fee'),
        ('equipment_rental', 'Equipment Rental'),
        ('filling_fee_certification', 'Filling Fee/Certification'),
        ('inspection_fee', 'Inspection Fee'),
        ('irrigation_services_fee', 'Irrigation Services Fee'),
        ('scraped_fix_assets', 'Scraped Fix Assets'),
        ('verification_authentication', 'Verification and Authentication'),
        ('bidding_documents', 'Bidding Documents'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    abc = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)  # Approved Budget for Contract
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Manually entered document price

    image = models.ImageField(upload_to='documents/', null=True, blank=True)
    region = models.CharField(max_length=250, default='Region IV-A')

    bidding_start_date = models.DateTimeField(null=True, blank=True)
    bidding_end_date = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[('open', 'Open'), ('closed', 'Closed'), ('awarded', 'Awarded')],
        default='open'
    )

    def __str__(self):
        return f"{self.title} - {self.category}"

    def check_bidding_status(self):
        """Update the bidding status based on current date."""
        now = timezone.now()
        if self.bidding_start_date and now < self.bidding_start_date:
            self.status = 'open'  # Or 'not_started' if you later add that option
        elif self.bidding_end_date and now > self.bidding_end_date:
            self.status = 'closed'
        else:
            self.status = 'open'
        self.save()


class Bid(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('under_review', 'Under Review'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='bids')
    proposed_price = models.DecimalField(max_digits=12, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')


    def set_price(self):
        return
    
    def __str__(self):
        return f"Bid by {self.user.username} on {self.document.title} for {self.proposed_price}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.quantity * self.document.price

    def __str__(self):
        return f"{self.user.username} - {self.document.title} ({self.quantity})"
    


