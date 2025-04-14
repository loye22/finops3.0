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


from django.shortcuts import render
from .models import Firm, Transaction, Bank, Partner, Subcategory
from django.db.models import Count, Q
from decimal import Decimal

def transaction_dashboard(request):
    # Get selected firm from query parameter
    selected_firm_id = request.GET.get('firm', 'all')

    # Fetch all firms
    firms = Firm.objects.all()

    # Initialize transactions queryset
    transactions = Transaction.objects.select_related('firm', 'bank', 'partner', 'subcategory')

    # Filter transactions by firm if not 'all'
    if selected_firm_id != 'all':
        transactions = transactions.filter(firm__id=selected_firm_id)

    # Calculate total uncategorized transactions
    total_uncategorized = transactions.filter(subcategory__name='N/A').count()

    # Calculate potential duplicates
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
        'transactions': transactions,
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




# # Set up logging
# logger = logging.getLogger(__name__)

# @login_required
# def upload_csv_view(request):
#     if request.method == 'POST':
#         form = CSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             csv_file = request.FILES['csv_file']
#             if not csv_file.name.endswith('.csv'):
#                 messages.error(request, 'Please upload a valid CSV file.')
#                 logger.error('Invalid file type: not a CSV')
#                 return redirect('upload_csv')

#             # Store the upload record
#             try:
#                 upload = Upload.objects.create(
#                     filename=csv_file.name,
#                     created_by=request.user.username,
#                     json_data={},
#                     sync_status='Pending',
#                     status='Uploaded'
#                 )
#                 logger.info(f"Created Upload record: {upload.id}")
#             except Exception as e:
#                 messages.error(request, f'Failed to create Upload record: {str(e)}')
#                 logger.error(f"Failed to create Upload: {str(e)}")
#                 return redirect('upload_csv')

#             try:
#                 # Read and process CSV
#                 file_data = csv_file.read().decode('utf-8')
#                 csv_reader = csv.DictReader(io.StringIO(file_data))

#                 # Log headers
#                 logger.info(f"CSV Headers: {csv_reader.fieldnames}")
#                 required_headers = ['Banca', 'Firma', 'IBAN Firma', 'Partener', 'IBAN Partener', 'Debit', 'Credit', 'Moneda', 'Detalii', 'Tip Suma']
#                 missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
#                 if missing_headers:
#                     messages.error(request, f'Missing CSV headers: {", ".join(missing_headers)}')
#                     logger.error(f'Missing headers: {missing_headers}')
#                     upload.sync_status = 'Failed'
#                     upload.status = 'Failed'
#                     upload.save()
#                     return redirect('upload_csv')

#                 # Find date column
#                 date_column = None
#                 possible_date_columns = ['Data', 'Date', 'data', 'date']
#                 for col in possible_date_columns:
#                     if col in csv_reader.fieldnames:
#                         date_column = col
#                         break

#                 if not date_column:
#                     messages.error(request, f'CSV file missing date column. Expected one of: {possible_date_columns}')
#                     logger.error(f'Missing date column. Headers: {csv_reader.fieldnames}')
#                     upload.sync_status = 'Failed'
#                     upload.status = 'Failed'
#                     upload.save()
#                     return redirect('upload_csv')

#                 # Get or create subcategory
#                 try:
#                     others_category, _ = Category.objects.get_or_create(name='Others')
#                     na_subcategory, _ = Subcategory.objects.get_or_create(
#                         name='N/A',
#                         category=others_category
#                     )
#                     logger.info("Found/Created Subcategory: N/A")
#                 except Exception as e:
#                     messages.error(request, f'Failed to create Subcategory: {str(e)}')
#                     logger.error(f"Failed to create Subcategory: {str(e)}")
#                     upload.sync_status = 'Failed'
#                     upload.status = 'Failed'
#                     upload.save()
#                     return redirect('upload_csv')

#                 row_count = 0
#                 success_count = 0
#                 duplicates = []

#                 for row in csv_reader:
#                     row_count += 1
#                     logger.info(f"Processing row {row_count}: {row}")

#                     # Check for missing date
#                     date_str = row.get(date_column, '').strip()
#                     if not date_str:
#                         logger.warning(f"Skipping row {row_count}: Missing date in column '{date_column}'")
#                         messages.warning(request, f"Skipped row {row_count}: Missing date")
#                         continue

#                     # Handle Bank
#                     bank_name = row.get('Banca', '').strip()
#                     if not bank_name:
#                         logger.warning(f"Skipping row {row_count}: Missing Banca name")
#                         messages.warning(request, f"Skipped row {row_count}: Missing Banca name")
#                         continue

#                     try:
#                         bank, created = Bank.objects.get_or_create(
#                             name=bank_name,
#                             defaults={'code': 'UNKNOWN'}  # Default code if new
#                         )
#                         if created:
#                             logger.info(f"Row {row_count}: Created Bank '{bank_name}' with code 'UNKNOWN'")
#                             messages.info(request, f"Created Bank '{bank_name}'")
#                         else:
#                             logger.info(f"Row {row_count}: Found Bank '{bank_name}'")
#                     except Exception as e:
#                         logger.warning(f"Skipping row {row_count}: Failed to create/get Bank: {str(e)}")
#                         messages.warning(request, f"Skipped row {row_count}: Failed to create/get Bank")
#                         continue

#                     # Handle Firm
#                     firm_name = row.get('Firma', '').strip()
#                     firm_iban = row.get('IBAN Firma', '').strip()
#                     if not firm_name:
#                         logger.warning(f"Skipping row {row_count}: Missing Firma name")
#                         messages.warning(request, f"Skipped row {row_count}: Missing Firma name")
#                         continue
#                     if not firm_iban:
#                         firm_iban = 'XXXXXXXXXXXXXXXXX'
#                         logger.info(f"Row {row_count}: Missing IBAN Firma, using default")

#                     try:
#                         firm, created = Firm.objects.get_or_create(
#                             name=firm_name,
#                             defaults={'iban': firm_iban}
#                         )
#                         if created:
#                             logger.info(f"Row {row_count}: Created Firm '{firm_name}' with IBAN '{firm_iban}'")
#                             messages.info(request, f"Created Firm '{firm_name}'")
#                         else:
#                             logger.info(f"Row {row_count}: Found Firm '{firm_name}'")
#                     except Exception as e:
#                         logger.warning(f"Skipping row {row_count}: Failed to create/get Firm: {str(e)}")
#                         messages.warning(request, f"Skipped row {row_count}: Failed to create/get Firm")
#                         continue

#                     # Handle Partner
#                     partner_name = row.get('Partener', '').strip()
#                     partner_iban = row.get('IBAN Partener', 'XXXXXXXXXXXXXXXXX').strip() or 'XXXXXXXXXXXXXXXXX'
#                     try:
#                         if partner_name:
#                             partner, _ = Partner.objects.get_or_create(
#                                 name=partner_name,
#                                 defaults={'iban': partner_iban}
#                             )
#                             logger.info(f"Row {row_count}: Found/Created Partner '{partner_name}'")
#                         else:
#                             partner, _ = Partner.objects.get_or_create(
#                                 name='Unknown Partner',
#                                 defaults={'iban': 'XXXXXXXXXXXXXXXXX'}
#                             )
#                             logger.info(f"Row {row_count}: Used default Unknown Partner")
#                     except Exception as e:
#                         logger.warning(f"Skipping row {row_count}: Failed to create/get Partner: {str(e)}")
#                         messages.warning(request, f"Skipped row {row_count}: Failed to create/get Partner")
#                         continue

#                     # Parse amount and type
#                     debit = row.get('Debit', '0').replace(',', '').replace('"', '').strip()
#                     credit = row.get('Credit', '0').replace(',', '').replace('"', '').strip()
#                     try:
#                         debit = Decimal(debit) if debit else Decimal('0.00')
#                         credit = Decimal(credit) if credit else Decimal('0.00')
#                         logger.debug(f"Row {row_count}: Parsed debit={debit}, credit={credit}")
#                     except (ValueError, TypeError) as e:
#                         logger.warning(f"Skipping row {row_count}: Invalid debit/credit format: {str(e)}")
#                         messages.warning(request, f"Skipped row {row_count}: Invalid debit/credit format")
#                         continue

#                     amount_type = row.get('Tip Suma', 'Debit').strip()
#                     if amount_type not in ['Debit', 'Credit']:
#                         logger.warning(f"Row {row_count}: Invalid amount_type '{amount_type}', defaulting to Debit")
#                         amount_type = 'Debit'

#                     # Parse date
#                     try:
#                         date = datetime.strptime(date_str, '%m/%d/%Y').date()
#                         logger.debug(f"Row {row_count}: Parsed date={date}")
#                     except ValueError as e:
#                         logger.warning(f"Skipping row {row_count}: Invalid date format '{date_str}': {str(e)}")
#                         messages.warning(request, f"Skipping row {row_count}: Invalid date format")
#                         continue

#                     # Check currency
#                     currency = row.get('Moneda', 'RON').strip()
#                     valid_currencies = ['USD', 'EUR', 'RON']
#                     if currency not in valid_currencies:
#                         logger.warning(f"Row {row_count}: Invalid currency '{currency}', defaulting to RON")
#                         currency = 'RON'

#                     # Check for duplicate transaction
#                     try:
#                         matching_transactions = Transaction.objects.filter(
#                             date=date,
#                             firm=firm,
#                             partner=partner,
#                             debit=debit,
#                             credit=credit,
#                             currency=currency
#                         )
#                         is_duplicate = matching_transactions.exists()
#                         match_details = [
#                             f"ID {t.id} (Date: {t.date}, Partner: {t.partner.name if t.partner else 'None'}, Debit: {t.debit}, Credit: {t.credit}, Currency: {t.currency})"
#                             for t in matching_transactions
#                         ]
#                     except Exception as e:
#                         logger.warning(f"Row {row_count}: Failed to check duplicates: {str(e)}")
#                         is_duplicate = False
#                         match_details = []

#                     if is_duplicate:
#                         duplicate_info = {
#                             'row': row_count,
#                             'date': date_str,
#                             'partner': partner_name or 'Unknown Partner',
#                             'debit': str(debit),
#                             'credit': str(credit),
#                             'currency': currency,
#                             'matches': match_details
#                         }
#                         duplicates.append(duplicate_info)
#                         logger.info(f"Row {row_count}: Flagged as duplicate - {duplicate_info}")
#                         messages.info(
#                             request,
#                             f"Row {row_count}: Flagged as duplicate "
#                             f"(Date: {date_str}, Partner: {partner_name or 'Unknown Partner'}, "
#                             f"Debit: {debit}, Credit: {credit}, Currency: {currency}) "
#                             f"matches transaction(s): {', '.join(match_details)}"
#                         )

#                     # Create transaction
#                     try:
#                         transaction = Transaction(
#                             date=date,
#                             bank=bank,
#                             firm=firm,
#                             partner=partner,
#                             debit=debit,
#                             credit=credit,
#                             currency=currency,
#                             details=row.get('Detalii', '').strip() or 'No details',
#                             notes=row.get('Observatii', '').strip(),
#                             subcategory=na_subcategory,
#                             transaction_type='N/A',
#                             amount_type=amount_type,
#                             verified=False,
#                             created_by=request.user.username,
#                             suspension_of_duplication=is_duplicate
#                         )
#                         transaction.full_clean()  # Validate before saving
#                         transaction.save()
#                         success_count += 1
#                         logger.info(f"Row {row_count}: Transaction created successfully{' (flagged as duplicate)' if is_duplicate else ''}")
#                     except Exception as e:
#                         logger.error(f"Row {row_count}: Failed to create transaction: {str(e)}")
#                         messages.error(request, f"Row {row_count}: Failed to create transaction: {str(e)}")
#                         continue

#                 # Summarize results
#                 if duplicates:
#                     duplicate_rows = [str(d['row']) for d in duplicates]
#                     messages.info(request, f"Flagged {len(duplicates)} duplicate rows: {', '.join(duplicate_rows)}")
#                     logger.info(f"Total duplicates flagged: {len(duplicates)}, Rows: {duplicate_rows}")
#                 else:
#                     messages.info(request, "No duplicate rows found.")
#                     logger.info("No duplicate rows found.")

#                 upload.sync_status = 'Synced' if success_count > 0 else 'Failed'
#                 upload.status = 'Processed' if success_count > 0 else 'Failed'
#                 upload.save()
#                 if success_count == 0:
#                     messages.error(request, f"No transactions were imported. Check logs for details.")
#                     logger.error(f"No transactions imported. Processed {row_count} rows.")
#                 else:
#                     messages.success(request, f"Imported {success_count} of {row_count} transactions successfully!")
#                     logger.info(f"Imported {success_count} of {row_count} transactions")

#                 return redirect('upload_csv')

#             except Exception as e:
#                 logger.error(f"CSV processing failed: {str(e)}")
#                 upload.sync_status = 'Failed'
#                 upload.status = 'Failed'
#                 upload.save()
#                 messages.error(request, f"Error processing CSV: {str(e)}")
#                 return redirect('upload_csv')

#     else:
#         form = CSVUploadForm()

#     return render(request, 'upload_csv.html', {'form': form})