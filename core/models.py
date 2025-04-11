from django.db import models

# Create your models here.
import uuid
from django.db import models

# Choices for ENUM fields
CURRENCY_CHOICES = (
    ('USD', 'USD'),
    ('EUR', 'EUR'),
    ('RON', 'RON'),
)

TRANSACTION_TYPE_CHOICES = (
    ('TRANSFER BANCAR', 'Transfer Bancar'),
    ('NUMERAR', 'Numerar'),
)

AMOUNT_TYPE_CHOICES = (
    ('Debit', 'Debit'),
    ('Credit', 'Credit'),
)

SYNC_STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Synced', 'Synced'),
    ('Failed', 'Failed'),
)

UPLOAD_STATUS_CHOICES = (
    ('Uploaded', 'Uploaded'),
    ('Processed', 'Processed'),
    ('Failed', 'Failed'),
)

class Firm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    iban = models.CharField(max_length=34, null=False, blank=False)  # Standard IBAN length

    class Meta:
        verbose_name = "Firm"
        verbose_name_plural = "Firms"
        db_table = "firms"

    def __str__(self):
        return self.name


class Bank(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    code = models.CharField(max_length=11, null=False, blank=False)  # BIC/SWIFT code length

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        db_table = "banks"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        db_table = "categories"

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories", null=False, blank=False)

    class Meta:
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"
        db_table = "subcategories"

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Partner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    iban = models.CharField(max_length=34, null=False, blank=False)

    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
        db_table = "partners"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(null=False, blank=False)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="transactions", null=False, blank=False)
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="transactions", null=False, blank=False)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, related_name="transactions", null=True, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, null=False, blank=False)
    credit = models.DecimalField(max_digits=15, decimal_places=2, null=False, blank=False)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, null=False, blank=False)
    details = models.TextField(null=False, blank=False)
    notes = models.TextField(null=True, blank=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name="transactions", null=False, blank=False)
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPE_CHOICES, 
        default='TRANSFER BANCAR', 
        null=False, 
        blank=False
    )
    amount_type = models.CharField(max_length=6, choices=AMOUNT_TYPE_CHOICES, null=False, blank=False)
    verified = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    created_by = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        db_table = "transactions"

    def __str__(self):
        return f"{self.date} - {self.firm.name} - {self.amount_type} {self.debit or self.credit} {self.currency}"


class Upload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    created_by = models.CharField(max_length=255, null=False, blank=False)
    json_data = models.JSONField(null=False, blank=False)
    sync_status = models.CharField(
        max_length=7, 
        choices=SYNC_STATUS_CHOICES, 
        default='Pending', 
        null=False, 
        blank=False
    )
    status = models.CharField(
        max_length=9, 
        choices=UPLOAD_STATUS_CHOICES, 
        default='Uploaded', 
        null=False, 
        blank=False
    )

    class Meta:
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
        db_table = "uploads"

    def __str__(self):
        return f"{self.filename} ({self.created_at}) - {self.sync_status}"