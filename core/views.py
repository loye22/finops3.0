import csv
import io
import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CSVUploadForm
from .models import Firm, Bank, Partner, Category, Subcategory, Transaction, Upload
from datetime import datetime
from django.core.paginator import Paginator

from django.shortcuts import render
from .models import Firm, Transaction, Bank, Partner, Subcategory
from django.db.models import Count, Q
from decimal import Decimal

def transaction_dashboard(request):
    # Get selected firm from query parameter
    selected_firm_id = request.GET.get('firm', 'all')

    # Fetch all firms
    firms = Firm.objects.all()

    # Initialize transactions queryset for display (filtered by firm if selected)
    transactions = Transaction.objects.select_related('firm', 'bank', 'partner', 'subcategory')

    # Filter transactions by firm if not 'all'
    if selected_firm_id != 'all':
        transactions = transactions.filter(firm__id=selected_firm_id)

    # Paginate transactions (200 per page)
    paginator = Paginator(transactions, 200)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Calculate total uncategorized transactions across ALL firms (not filtered by firm)
    total_uncategorized = Transaction.objects.filter(subcategory__name='N/A').count()

    # Calculate potential duplicates (filtered by firm if selected)
    total_duplicates = transactions.filter(suspension_of_duplication=True).count()

    # Add uncategorized count to each firm
    for firm in firms:
        firm.uncategorized_count = Transaction.objects.filter(
            firm=firm, subcategory__name='N/A'
        ).count()

    # Unique values for filters
    unique_dates = transactions.values_list('date', flat=True).distinct()
    unique_banks = transactions.values_list('bank__name', flat=True).distinct()
    unique_firms = transactions.values_list('firm__name', flat=True).distinct()
    unique_partners = transactions.values_list('partner__name', flat=True).distinct()
    unique_debits = transactions.values_list('debit', flat=True).distinct()
    unique_credits = transactions.values_list('credit', flat=True).distinct()
    unique_currencies = transactions.values_list('currency', flat=True).distinct()
    unique_subcategories = transactions.values_list('subcategory__name', flat=True).distinct()

    context = {
        'firms': firms,
        'page_obj': page_obj,
        'total_uncategorized': total_uncategorized,
        'total_duplicates': total_duplicates,
        'selected_firm': selected_firm_id,
        'unique_dates': unique_dates,
        'unique_banks': unique_banks,
        'unique_firms': unique_firms,
        'unique_partners': unique_partners,
        'unique_debits': unique_debits,
        'unique_credits': unique_credits,
        'unique_currencies': unique_currencies,
        'unique_subcategories': unique_subcategories,
    }

    return render(request, 'home.html', context)