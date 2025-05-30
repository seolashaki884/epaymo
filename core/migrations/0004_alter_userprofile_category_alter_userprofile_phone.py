# Generated by Django 5.2 on 2025-05-15 00:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userprofile_address_userprofile_phone_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='category',
            field=models.CharField(choices=[('drainage_fee', 'Drainage Fee'), ('equipment_rental', 'Equipment Rental'), ('filling_fee_certification', 'Filling Fee/Certification'), ('inspection_fee', 'Inspection Fee'), ('irrigation_services_fee', 'Irrigation Services Fee'), ('scraped_fix_assets', 'Scraped Fix Assets'), ('verification_authentication', 'Verification and Authentication'), ('bidding_documents', 'Bidding Documents')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.BigIntegerField(null=True),
        ),
    ]
