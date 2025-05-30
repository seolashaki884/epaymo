# Generated by Django 5.2 on 2025-05-09 06:16

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('drainage_fee', 'Drainage Fee'), ('equipment_rental', 'Equipment Rental'), ('filling_fee_certification', 'Filling Fee/Certification'), ('inspection_fee', 'Inspection Fee'), ('irrigation_services_fee', 'Irrigation Services Fee'), ('scraped_fix_assets', 'Scraped Fix Assets'), ('verification_authentication', 'Verification and Authentication'), ('bidding_documents', 'Bidding Documents')], max_length=50)),
                ('abc', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to='documents/')),
                ('region', models.CharField(default='Region IV-A', max_length=250)),
                ('bidding_start_date', models.DateTimeField(blank=True, null=True)),
                ('bidding_end_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('closed', 'Closed'), ('awarded', 'Awarded')], default='open', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proposed_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('bid_time', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('under_review', 'Under Review'), ('rejected', 'Rejected'), ('paid', 'Paid')], default='pending', max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='core.document')),
            ],
        ),
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('email_add', models.CharField(max_length=255)),
                ('number', models.BigIntegerField(null=True)),
                ('invoice_number', models.CharField(max_length=100, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending Verification'), ('paid', 'Paid'), ('unpaid', 'Unpaid')], default='pending', max_length=50)),
                ('issued_date', models.DateField(default=django.utils.timezone.now)),
                ('bid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='billing', to='core.bid')),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.document')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('drainage_fee', 'Drainage Fee'), ('equipment_rental', 'Equipment Rental'), ('filling_fee_certification', 'Filling Fee/Certification'), ('inspection_fee', 'Inspection Fee'), ('irrigation_services_fee', 'Irrigation Services Fee'), ('scraped_fix_assets', 'Scraped Fix Assets'), ('verification_authentication', 'Verification and Authentication'), ('bidding_documents', 'Bidding Documents')], max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
