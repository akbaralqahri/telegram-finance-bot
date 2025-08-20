"""
Google Sheets service for Finance Bot
Handles all Google Sheets operations for financial data storage
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import Config
from utils.helpers import parse_amount, detect_transaction_category

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for managing Google Sheets operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        self.gc = None
        self.service = None
        self.credentials = None
        self.user_sheets = {}  # Cache for user spreadsheets
        
    async def initialize(self):
        """Initialize Google Sheets service"""
        try:
            self.credentials = self._get_credentials()
            self.gc = gspread.authorize(self.credentials)
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheets service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            return False
    
    def _get_credentials(self):
        """Get or refresh Google credentials"""
        creds = None
        
        # Load existing token
        if os.path.exists(Config.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.CREDENTIALS_FILE, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(Config.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    async def initialize_user_sheet(self, user_id: int, user_name: str) -> bool:
        """Initialize spreadsheet for a new user"""
        try:
            if not self.gc:
                await self.initialize()
            
            # Check if user already has a spreadsheet
            if user_id in self.user_sheets:
                return True
            
            # Create or get existing spreadsheet
            spreadsheet_name = f"{Config.SPREADSHEET_NAME} - {user_name} ({user_id})"
            
            try:
                # Try to open existing spreadsheet
                spreadsheet = self.gc.open(spreadsheet_name)
                logger.info(f"Found existing spreadsheet for user {user_id}")
                
                # Verify and fix sheet structure if needed
                await self._verify_and_fix_sheet_structure(spreadsheet)
                
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                spreadsheet = self.gc.create(spreadsheet_name)
                logger.info(f"Created new spreadsheet for user {user_id}")
                
                # Setup initial sheets and headers
                await self._setup_initial_sheets(spreadsheet)
            
            # Cache the spreadsheet
            self.user_sheets[user_id] = spreadsheet
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing user sheet for {user_id}: {e}")
            return False
    
    async def _verify_and_fix_sheet_structure(self, spreadsheet):
        """Verify and fix existing spreadsheet structure"""
        try:
            # Check if Transactions sheet exists and has proper headers
            try:
                transactions_sheet = spreadsheet.worksheet('Transactions')
                
                # Get first row to check headers
                first_row = transactions_sheet.row_values(1)
                expected_headers = Config.TRANSACTION_HEADERS
                
                # If headers don't match, update them
                if first_row != expected_headers:
                    logger.info("Updating transaction headers")
                    transactions_sheet.update('1:1', [expected_headers])
                    
            except gspread.WorksheetNotFound:
                # Rename first sheet to Transactions if it doesn't exist
                logger.info("Creating Transactions sheet")
                transactions_sheet = spreadsheet.sheet1
                transactions_sheet.update_title('Transactions')
                transactions_sheet.update('1:1', [Config.TRANSACTION_HEADERS])
            
            # Check Categories sheet
            try:
                categories_sheet = spreadsheet.worksheet('Categories')
                first_row = categories_sheet.row_values(1)
                if first_row != Config.CATEGORY_HEADERS:
                    categories_sheet.update('1:1', [Config.CATEGORY_HEADERS])
            except gspread.WorksheetNotFound:
                logger.info("Creating Categories sheet")
                categories_sheet = spreadsheet.add_worksheet(title='Categories', rows=100, cols=10)
                categories_sheet.update('1:1', [Config.CATEGORY_HEADERS])
                
                # Add default categories
                for cat_type, categories in Config.DEFAULT_CATEGORIES.items():
                    for cat in categories:
                        categories_sheet.append_row([
                            cat['name'],
                            cat_type,
                            ','.join(cat['keywords']),
                            cat['icon']
                        ])
            
            # Check Monthly Summary sheet
            try:
                summary_sheet = spreadsheet.worksheet('Monthly_Summary')
                first_row = summary_sheet.row_values(1)
                if first_row != Config.SUMMARY_HEADERS:
                    summary_sheet.update('1:1', [Config.SUMMARY_HEADERS])
            except gspread.WorksheetNotFound:
                logger.info("Creating Monthly_Summary sheet")
                summary_sheet = spreadsheet.add_worksheet(title='Monthly_Summary', rows=100, cols=10)
                summary_sheet.update('1:1', [Config.SUMMARY_HEADERS])
            
            logger.info("Sheet structure verified and fixed")
            
        except Exception as e:
            logger.error(f"Error verifying sheet structure: {e}")
            raise
    
    async def _setup_initial_sheets(self, spreadsheet):
        """Setup initial sheets with headers and sample data"""
        try:
            # Get default sheet and rename to 'Transactions'
            transactions_sheet = spreadsheet.sheet1
            transactions_sheet.update_title('Transactions')
            
            # Add headers to transactions sheet
            transactions_sheet.update('1:1', [Config.TRANSACTION_HEADERS])
            
            # Create Categories sheet
            categories_sheet = spreadsheet.add_worksheet(title='Categories', rows=100, cols=10)
            categories_sheet.update('1:1', [Config.CATEGORY_HEADERS])
            
            # Add default categories
            for cat_type, categories in Config.DEFAULT_CATEGORIES.items():
                for cat in categories:
                    categories_sheet.append_row([
                        cat['name'],
                        cat_type,
                        ','.join(cat['keywords']),
                        cat['icon']
                    ])
            
            # Create Summary sheet
            summary_sheet = spreadsheet.add_worksheet(title='Monthly_Summary', rows=100, cols=10)
            summary_sheet.update('1:1', [Config.SUMMARY_HEADERS])
            
            # Format headers (make them bold)
            for sheet in [transactions_sheet, categories_sheet, summary_sheet]:
                sheet.format('1:1', {'textFormat': {'bold': True}})
            
            logger.info("Initial sheets setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up initial sheets: {e}")
            raise
    
    async def add_transaction(self, user_id: int, amount: float, description: str, 
                            category: str, transaction_type: str) -> bool:
        """Add a new transaction to user's spreadsheet"""
        try:
            # Ensure user sheet exists
            if user_id not in self.user_sheets:
                success = await self.initialize_user_sheet(user_id, f"User_{user_id}")
                if not success:
                    return False
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get current balance
            current_balance = await self.get_user_balance(user_id)
            
            # Calculate new balance
            if transaction_type == 'income':
                new_balance = current_balance + amount
                income_amount = amount
                expense_amount = ''
            else:
                new_balance = current_balance - amount
                income_amount = ''
                expense_amount = amount
            
            # Prepare row data
            now = datetime.now()
            row_data = [
                now.strftime('%Y-%m-%d'),  # Date
                now.strftime('%H:%M:%S'),  # Time
                category,                  # Category
                description,              # Description
                income_amount,            # Income
                expense_amount,           # Expense
                new_balance,             # Balance
                user_id                  # User ID
            ]
            
            # Add transaction
            transactions_sheet.append_row(row_data)
            
            # Update monthly summary
            await self._update_monthly_summary(user_id, amount, transaction_type, now)
            
            logger.info(f"Transaction added for user {user_id}: {transaction_type} {amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding transaction for user {user_id}: {e}")
            return False
    
    async def get_user_balance(self, user_id: int) -> float:
        """Get current balance for user"""
        try:
            if user_id not in self.user_sheets:
                return 0.0
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all values instead of records to avoid parsing issues
            all_values = transactions_sheet.get_all_values()
            
            # Check if there are any data rows (more than just header)
            if len(all_values) <= 1:
                logger.info(f"No transaction data for user {user_id}, returning balance 0")
                return 0.0
            
            # Get the last row (skip header at index 0)
            data_rows = all_values[1:]  # Skip header
            if not data_rows:
                return 0.0
            
            # Find the last non-empty row
            last_row = None
            for row in reversed(data_rows):
                if any(cell.strip() for cell in row if cell):  # Check if row has any non-empty cells
                    last_row = row
                    break
            
            if not last_row or len(last_row) < 7:  # Balance is at index 6
                return 0.0
            
            # Get balance from last row (index 6 is Saldo column)
            balance_str = last_row[6] if len(last_row) > 6 else '0'
            
            if not balance_str or balance_str.strip() == '':
                return 0.0
            
            # Parse balance
            balance = parse_amount(balance_str)
            return float(balance) if balance is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error getting balance for user {user_id}: {e}")
            return 0.0
    
    async def get_monthly_summary(self, user_id: int, year: int, month: int) -> Dict:
        """Get monthly financial summary"""
        try:
            if user_id not in self.user_sheets:
                return {'income': 0, 'expense': 0, 'net': 0}
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all values instead of records
            all_values = transactions_sheet.get_all_values()
            
            # Check if there are any data rows
            if len(all_values) <= 1:
                logger.info(f"No transaction data for user {user_id} in {month}/{year}")
                return {'income': 0, 'expense': 0, 'net': 0}
            
            # Get headers and data
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Find column indices
            try:
                date_idx = headers.index('Tanggal')
                income_idx = headers.index('Pemasukan')
                expense_idx = headers.index('Pengeluaran')
            except ValueError as e:
                logger.error(f"Header not found: {e}")
                return {'income': 0, 'expense': 0, 'net': 0}
            
            total_income = 0
            total_expense = 0
            
            for row in data_rows:
                if len(row) <= max(date_idx, income_idx, expense_idx):
                    continue
                
                try:
                    # Parse date
                    date_str = row[date_idx] if date_idx < len(row) else ''
                    if not date_str or date_str.strip() == '':
                        continue
                        
                    record_date = datetime.strptime(date_str.strip(), '%Y-%m-%d')
                    
                    if record_date.year == year and record_date.month == month:
                        # Parse income and expense
                        income_str = row[income_idx] if income_idx < len(row) else ''
                        expense_str = row[expense_idx] if expense_idx < len(row) else ''
                        
                        income = parse_amount(income_str) if income_str and income_str.strip() else 0
                        expense = parse_amount(expense_str) if expense_str and expense_str.strip() else 0
                        
                        total_income += income or 0
                        total_expense += expense or 0
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing row for user {user_id}: {e}")
                    continue
            
            return {
                'income': total_income,
                'expense': total_expense,
                'net': total_income - total_expense
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary for user {user_id}: {e}")
            return {'income': 0, 'expense': 0, 'net': 0}
    
    async def generate_report(self, user_id: int, report_type: str = 'monthly') -> Dict:
        """Generate financial report"""
        try:
            if user_id not in self.user_sheets:
                return self._empty_report(report_type)
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all values instead of records
            all_values = transactions_sheet.get_all_values()
            
            # Check if there are any data rows
            if len(all_values) <= 1:
                logger.info(f"No transaction data for user {user_id} report")
                return self._empty_report(report_type)
            
            # Convert to records format for easier processing
            headers = all_values[0]
            records = []
            for row in all_values[1:]:
                if len(row) >= len(headers):
                    record = dict(zip(headers, row))
                    records.append(record)
            
            # Filter records based on report type
            filtered_records = self._filter_records_by_period(records, report_type)
            
            # Calculate totals
            total_income = 0
            total_expense = 0
            category_expenses = {}
            transactions = []
            
            for record in filtered_records:
                try:
                    income_str = str(record.get('Pemasukan', ''))
                    expense_str = str(record.get('Pengeluaran', ''))
                    
                    income = parse_amount(income_str) if income_str and income_str.strip() else 0
                    expense = parse_amount(expense_str) if expense_str and expense_str.strip() else 0
                    category = record.get('Kategori', 'Lainnya')
                    
                    total_income += income or 0
                    total_expense += expense or 0
                    
                    # Track category expenses
                    if expense and expense > 0:
                        category_expenses[category] = category_expenses.get(category, 0) + expense
                    
                    # Add to transactions list
                    if income and income > 0:
                        amount = income
                    elif expense and expense > 0:
                        amount = -expense
                    else:
                        continue
                        
                    transactions.append({
                        'date': record.get('Tanggal', ''),
                        'category': category,
                        'description': record.get('Deskripsi', ''),
                        'amount': amount
                    })
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing record for user {user_id}: {e}")
                    continue
            
            # Sort category expenses
            top_expenses = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
            
            # Get current balance
            current_balance = await self.get_user_balance(user_id)
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_amount': total_income - total_expense,
                'current_balance': current_balance,
                'top_expenses': top_expenses,
                'transactions': transactions,
                'period': report_type
            }
            
        except Exception as e:
            logger.error(f"Error generating report for user {user_id}: {e}")
            return self._empty_report(report_type)
    
    def _empty_report(self, report_type: str) -> Dict:
        """Return empty report structure"""
        return {
            'total_income': 0,
            'total_expense': 0,
            'net_amount': 0,
            'current_balance': 0,
            'top_expenses': [],
            'transactions': [],
            'period': report_type
        }
    
    async def search_transactions(self, user_id: int, query: str) -> List[Dict]:
        """Search transactions based on query"""
        try:
            if user_id not in self.user_sheets:
                return []
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all values
            all_values = transactions_sheet.get_all_values()
            
            if len(all_values) <= 1:
                return []
            
            # Convert to records
            headers = all_values[0]
            records = []
            for row in all_values[1:]:
                if len(row) >= len(headers):
                    record = dict(zip(headers, row))
                    records.append(record)
            
            results = []
            query_lower = query.lower()
            
            for record in records:
                try:
                    # Search in description, category, and amount
                    description = str(record.get('Deskripsi', '')).lower()
                    category = str(record.get('Kategori', '')).lower()
                    income = str(record.get('Pemasukan', ''))
                    expense = str(record.get('Pengeluaran', ''))
                    
                    # Check if query matches
                    if (query_lower in description or 
                        query_lower in category or 
                        query in income or 
                        query in expense):
                        
                        income_val = parse_amount(income) if income and income.strip() else 0
                        expense_val = parse_amount(expense) if expense and expense.strip() else 0
                        amount = income_val if income_val and income_val > 0 else -(expense_val or 0)
                        
                        results.append({
                            'date': record.get('Tanggal', ''),
                            'category': record.get('Kategori', ''),
                            'description': record.get('Deskripsi', ''),
                            'amount': amount
                        })
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing search record for user {user_id}: {e}")
                    continue
            
            # Sort by date (newest first)
            results.sort(key=lambda x: x['date'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching transactions for user {user_id}: {e}")
            return []
    
    async def get_daily_transactions(self, user_id: int, date: datetime = None) -> List[Dict]:
        """Get transactions for a specific day"""
        try:
            if not date:
                date = datetime.now()
            
            if user_id not in self.user_sheets:
                return []
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all values
            all_values = transactions_sheet.get_all_values()
            
            if len(all_values) <= 1:
                return []
            
            # Convert to records
            headers = all_values[0]
            records = []
            for row in all_values[1:]:
                if len(row) >= len(headers):
                    record = dict(zip(headers, row))
                    records.append(record)
            
            target_date = date.strftime('%Y-%m-%d')
            daily_transactions = []
            
            for record in records:
                if record.get('Tanggal') == target_date:
                    income_str = str(record.get('Pemasukan', ''))
                    expense_str = str(record.get('Pengeluaran', ''))
                    
                    income = parse_amount(income_str) if income_str and income_str.strip() else 0
                    expense = parse_amount(expense_str) if expense_str and expense_str.strip() else 0
                    amount = income if income and income > 0 else -(expense or 0)
                    
                    daily_transactions.append({
                        'date': record.get('Tanggal', ''),
                        'time': record.get('Waktu', ''),
                        'category': record.get('Kategori', ''),
                        'description': record.get('Deskripsi', ''),
                        'amount': amount
                    })
            
            return daily_transactions
            
        except Exception as e:
            logger.error(f"Error getting daily transactions for user {user_id}: {e}")
            return []
    
    async def detect_category(self, description: str, transaction_type: str) -> str:
        """Auto-detect category based on transaction description"""
        try:
            # Use helper function to detect category
            return detect_transaction_category(description, transaction_type)
            
        except Exception as e:
            logger.error(f"Error detecting category: {e}")
            return 'Lainnya'
    
    async def get_user_categories(self, user_id: int) -> List[Dict]:
        """Get user's categories"""
        try:
            if user_id not in self.user_sheets:
                return []
            
            spreadsheet = self.user_sheets[user_id]
            
            try:
                categories_sheet = spreadsheet.worksheet('Categories')
                all_values = categories_sheet.get_all_values()
                
                if len(all_values) <= 1:
                    return []
                
                # Convert to records
                headers = all_values[0]
                categories = []
                for row in all_values[1:]:
                    if len(row) >= len(headers):
                        record = dict(zip(headers, row))
                        categories.append(record)
                
                return categories
                
            except gspread.WorksheetNotFound:
                logger.warning(f"Categories sheet not found for user {user_id}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {e}")
            return []
    
    async def get_user_financial_summary(self, user_id: int) -> Dict:
        """Get comprehensive financial summary for AI analysis"""
        try:
            current_balance = await self.get_user_balance(user_id)
            
            # Get current month summary
            now = datetime.now()
            monthly_summary = await self.get_monthly_summary(user_id, now.year, now.month)
            
            # Get last month for comparison
            last_month = now.replace(day=1) - timedelta(days=1)
            last_month_summary = await self.get_monthly_summary(user_id, last_month.year, last_month.month)
            
            # Get recent transactions
            recent_transactions = await self.get_daily_transactions(user_id)
            
            # Generate report for category analysis
            monthly_report = await self.generate_report(user_id, 'monthly')
            
            return {
                'current_balance': current_balance,
                'this_month': monthly_summary,
                'last_month': last_month_summary,
                'recent_transactions': recent_transactions,
                'top_categories': monthly_report.get('top_expenses', []),
                'net_this_month': monthly_summary.get('net', 0),
                'net_last_month': last_month_summary.get('net', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting financial summary for user {user_id}: {e}")
            return {
                'current_balance': 0,
                'this_month': {'income': 0, 'expense': 0, 'net': 0},
                'last_month': {'income': 0, 'expense': 0, 'net': 0},
                'recent_transactions': [],
                'top_categories': [],
                'net_this_month': 0,
                'net_last_month': 0
            }
    
    async def _update_monthly_summary(self, user_id: int, amount: float, 
                                    transaction_type: str, date: datetime):
        """Update monthly summary sheet"""
        try:
            spreadsheet = self.user_sheets[user_id]
            
            try:
                summary_sheet = spreadsheet.worksheet('Monthly_Summary')
            except gspread.WorksheetNotFound:
                logger.warning(f"Monthly_Summary sheet not found for user {user_id}")
                return
            
            period_key = f"{date.year}-{date.month:02d}"
            
            # Get all values
            all_values = summary_sheet.get_all_values()
            
            if len(all_values) <= 1:
                # No data, create first record
                if transaction_type == 'income':
                    income = amount
                    expense = 0
                else:
                    income = 0
                    expense = amount
                
                balance = income - expense
                summary_sheet.append_row([period_key, income, expense, balance, user_id])
                return
            
            # Convert to records
            headers = all_values[0]
            records = []
            for i, row in enumerate(all_values[1:], start=2):  # Start from row 2 (1-indexed)
                if len(row) >= len(headers):
                    record = dict(zip(headers, row))
                    record['_row_number'] = i
                    records.append(record)
            
            # Find existing record for this month
            existing_record = None
            for record in records:
                if record.get('Periode') == period_key:
                    existing_record = record
                    break
            
            if existing_record:
                # Update existing record
                current_income = parse_amount(str(existing_record.get('Total Pemasukan', ''))) or 0
                current_expense = parse_amount(str(existing_record.get('Total Pengeluaran', ''))) or 0
                
                if transaction_type == 'income':
                    new_income = current_income + amount
                    new_expense = current_expense
                else:
                    new_income = current_income
                    new_expense = current_expense + amount
                
                new_balance = new_income - new_expense
                
                # Update the row
                row_number = existing_record['_row_number']
                summary_sheet.update(f'B{row_number}:D{row_number}', [[new_income, new_expense, new_balance]])
            else:
                # Create new record
                if transaction_type == 'income':
                    income = amount
                    expense = 0
                else:
                    income = 0
                    expense = amount
                
                balance = income - expense
                summary_sheet.append_row([period_key, income, expense, balance, user_id])
            
        except Exception as e:
            logger.error(f"Error updating monthly summary: {e}")
    
    def _filter_records_by_period(self, records: List[Dict], period: str) -> List[Dict]:
        """Filter records based on time period"""
        now = datetime.now()
        filtered = []
        
        for record in records:
            try:
                date_str = record.get('Tanggal', '')
                if not date_str:
                    continue
                    
                record_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if period == 'daily':
                    if record_date.date() == now.date():
                        filtered.append(record)
                elif period == 'weekly':
                    start_week = now - timedelta(days=now.weekday())
                    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
                    if record_date >= start_week:
                        filtered.append(record)
                elif period == 'monthly':
                    if record_date.year == now.year and record_date.month == now.month:
                        filtered.append(record)
                elif period == 'yearly':
                    if record_date.year == now.year:
                        filtered.append(record)
                        
            except ValueError as e:
                logger.warning(f"Error parsing date in record: {e}")
                continue
        
        return filtered