from django.contrib import admin
from .models import (
    Firm, Bank, Category, Subcategory, Partner,
    Transaction, Upload
)

@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ('name', 'iban')
    search_fields = ('name', 'iban')

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'iban')
    search_fields = ('name', 'iban')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'firm', 'bank', 'amount_type', 'debit', 'credit', 'currency', 'verified')
    list_filter = ('date', 'bank', 'firm', 'currency', 'transaction_type', 'amount_type', 'verified' , 'suspension_of_duplication')
    search_fields = ('firm__name', 'bank__name', 'partner__name', 'details')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'created_at', 'created_by', 'sync_status', 'status')
    list_filter = ('sync_status', 'status', 'created_at')
    search_fields = ('filename', 'created_by')
    readonly_fields = ('created_at',)
