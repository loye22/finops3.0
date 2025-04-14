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

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def upload_csv_view(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('upload_csv')

            # Store the upload record
            upload = Upload.objects.create(
                filename=csv_file.name,
                created_by=request.user.username,
                json_data={},  # We'll update this if needed
                sync_status='Pending',
                status='Uploaded'
            )

            try:
                # Read and process CSV
                file_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(file_data))

                # Log headers for debugging
                logger.info(f"CSV Headers: {csv_reader.fieldnames}")

                # Find date column dynamically
                date_column = None
                possible_date_columns = ['Data', 'Date', 'data', 'date']
                for col in possible_date_columns:
                    if col in csv_reader.fieldnames:
                        date_column = col
                        break

                if not date_column:
                    messages.error(request, f'CSV file missing date column. Expected one of: {possible_date_columns}')
                    logger.error(f'CSV file missing date column. Headers: {csv_reader.fieldnames}')
                    upload.sync_status = 'Failed'
                    upload.status = 'Failed'
                    upload.save()
                    return redirect('upload_csv')

                # Get or create required objects
                try:
                    bank = Bank.objects.get(name='First Bank')
                    firm = Firm.objects.get(name='IFIGENIA')
                    others_category, _ = Category.objects.get_or_create(name='Others')
                    na_subcategory, _ = Subcategory.objects.get_or_create(
                        name='N/A',
                        category=others_category
                    )
                except Bank.DoesNotExist:
                    messages.error(request, 'Bank "First Bank" not found in database.')
                    upload.sync_status = 'Failed'
                    upload.status = 'Failed'
                    upload.save()
                    return redirect('upload_csv')
                except Firm.DoesNotExist:
                    messages.error(request, 'Firm "IFIGENIA" not found in database.')
                    upload.sync_status = 'Failed'
                    upload.status = 'Failed'
                    upload.save()
                    return redirect('upload_csv')

                row_count = 0
                success_count = 0
                duplicates = []  # Track duplicate rows and their matches

                for row in csv_reader:
                    row_count += 1
                    logger.info(f"Processing row {row_count}: {row}")

                    # Check for missing date
                    date_str = row.get(date_column, '').strip()
                    if not date_str:
                        logger.warning(f"Skipping row {row_count}: Missing date in column '{date_column}' - Row content: {row}")
                        messages.warning(request, f"Skipped row {row_count}: Missing date")
                        continue

                    # Handle Partner
                    partner_name = row.get('Partener', '').strip()
                    partner_iban = row.get('IBAN Partener', 'XXXXXXXXXXXXXXXXX').strip() or 'XXXXXXXXXXXXXXXXX'
                    if partner_name:
                        partner, _ = Partner.objects.get_or_create(
                            name=partner_name,
                            defaults={'iban': partner_iban}
                        )
                    else:
                        partner, _ = Partner.objects.get_or_create(
                            name='Unknown Partner',
                            defaults={'iban': 'XXXXXXXXXXXXXXXXX'}
                        )
                        logger.info(f"Row {row_count}: Created default Unknown Partner")

                    # Parse amount and type
                    debit = row.get('Debit', '0').replace(',', '').replace('"', '').strip()
                    credit = row.get('Credit', '0').replace(',', '').replace('"', '').strip()
                    try:
                        debit = Decimal(debit) if debit else Decimal('0.00')
                        credit = Decimal(credit) if credit else Decimal('0.00')
                    except (ValueError, TypeError):
                        logger.warning(f"Skipping row {row_count}: Invalid debit/credit format")
                        messages.warning(request, f"Skipped row {row_count}: Invalid debit/credit format")
                        continue

                    amount_type = row.get('Tip Suma', 'Debit').strip()
                    if amount_type not in ['Debit', 'Credit']:
                        logger.warning(f"Row {row_count}: Invalid amount_type, defaulting to Debit")
                        amount_type = 'Debit'

                    # Parse date
                    try:
                        date = datetime.strptime(date_str, '%m/%d/%Y').date()
                    except ValueError:
                        logger.warning(f"Skipping row {row_count}: Invalid date format: {date_str}")
                        messages.warning(request, f"Skipped row {row_count}: Invalid date format")
                        continue

                    # Check for duplicate transaction
                    currency = row.get('Moneda', 'RON').strip()
                    matching_transactions = Transaction.objects.filter(
                        date=date,
                        firm=firm,
                        partner=partner,
                        debit=debit,
                        credit=credit,
                        currency=currency
                    )
                    is_duplicate = matching_transactions.exists()
                    match_details = [
                        f"ID {t.id} (Date: {t.date}, Partner: {t.partner.name if t.partner else 'None'}, Debit: {t.debit}, Credit: {t.credit}, Currency: {t.currency})"
                        for t in matching_transactions
                    ]

                    if is_duplicate:
                        duplicate_info = {
                            'row': row_count,
                            'date': date_str,
                            'partner': partner_name or 'Unknown Partner',
                            'debit': str(debit),
                            'credit': str(credit),
                            'currency': currency,
                            'matches': match_details
                        }
                        duplicates.append(duplicate_info)
                        logger.info(f"Row {row_count}: Flagged as duplicate - {duplicate_info}")
                        messages.info(
                            request,
                            f"Row {row_count}: Flagged as duplicate "
                            f"(Date: {date_str}, Partner: {partner_name or 'Unknown Partner'}, "
                            f"Debit: {debit}, Credit: {credit}, Currency: {currency}) "
                            f"matches transaction(s): {', '.join(match_details)}"
                        )

                    # Create transaction (even if duplicate, with flag set)
                    try:
                        Transaction.objects.create(
                            date=date,
                            bank=bank,
                            firm=firm,
                            partner=partner,
                            debit=debit,
                            credit=credit,
                            currency=currency,
                            details=row.get('Detalii', '').strip() or 'No details',
                            notes=row.get('Observatii', '').strip(),
                            subcategory=na_subcategory,
                            transaction_type='N/A',
                            amount_type=amount_type,
                            verified=False,
                            created_by=request.user.username,
                            suspension_of_duplication=is_duplicate
                        )
                        success_count += 1
                        logger.info(f"Row {row_count}: Transaction created successfully{' (flagged as duplicate)' if is_duplicate else ''}")
                    except Exception as e:
                        logger.error(f"Row {row_count}: Failed to create transaction: {str(e)}")
                        messages.error(request, f"Row {row_count}: Failed to create transaction: {str(e)}")

                # Summarize duplicates in UI and logs
                if duplicates:
                    duplicate_rows = [str(d['row']) for d in duplicates]
                    messages.info(request, f"Flagged {len(duplicates)} duplicate rows: {', '.join(duplicate_rows)}")
                    logger.info(f"Total duplicates flagged: {len(duplicates)}, Rows: {duplicate_rows}")
                else:
                    messages.info(request, "No duplicate rows found.")
                    logger.info("No duplicate rows found.")

                upload.sync_status = 'Synced' if success_count > 0 else 'Failed'
                upload.status = 'Processed' if success_count > 0 else 'Failed'
                upload.save()
                messages.success(request, f'Imported {success_count} of {row_count} transactions successfully!')
                return redirect('upload_csv')

            except Exception as e:
                logger.error(f"CSV processing failed: {str(e)}")
                upload.sync_status = 'Failed'
                upload.status = 'Failed'
                upload.save()
                messages.error(request, f'Error processing CSV: {str(e)}')
                return redirect('upload_csv')

    else:
        form = CSVUploadForm()

    return render(request, 'upload_csv.html', {'form': form})