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
    
    async def _setup_initial_sheets(self, spreadsheet):
        """Setup initial sheets with headers and sample data"""
        try:
            # Get default sheet and rename to 'Transactions'
            transactions_sheet = spreadsheet.sheet1
            transactions_sheet.update_title('Transactions')
            
            # Add headers to transactions sheet
            transactions_sheet.append_row(Config.TRANSACTION_HEADERS)
            
            # Create Categories sheet
            categories_sheet = spreadsheet.add_worksheet(title='Categories', rows=100, cols=10)
            categories_sheet.append_row(Config.CATEGORY_HEADERS)
            
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
            summary_sheet.append_row(Config.SUMMARY_HEADERS)
            
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
            
            # Get all records
            records = transactions_sheet.get_all_records()
            
            if not records:
                return 0.0
            
            # Get the last balance value
            last_record = records[-1]
            balance = last_record.get('Saldo', 0)
            
            # Convert to float if it's a string
            if isinstance(balance, str):
                balance = parse_amount(balance) or 0
            
            return float(balance)
            
        except Exception as e:
            logger.error(f"Error getting balance for user {user_id}: {e}")
            return 0.0
    
    async def get_monthly_summary(self, user_id: int, year: int, month: int) -> Dict:
        """Get monthly financial summary"""
        try:
            if user_id not in self.user_sheets:
                return {'income': 0, 'expense': 0, 'balance': 0}
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            
            # Get all records for the specified month
            records = transactions_sheet.get_all_records()
            
            total_income = 0
            total_expense = 0
            
            for record in records:
                try:
                    # Parse date
                    record_date = datetime.strptime(record['Tanggal'], '%Y-%m-%d')
                    
                    if record_date.year == year and record_date.month == month:
                        income = parse_amount(str(record.get('Pemasukan', ''))) or 0
                        expense = parse_amount(str(record.get('Pengeluaran', ''))) or 0
                        
                        total_income += income
                        total_expense += expense
                        
                except (ValueError, KeyError):
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
                return {}
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            records = transactions_sheet.get_all_records()
            
            # Filter records based on report type
            filtered_records = self._filter_records_by_period(records, report_type)
            
            # Calculate totals
            total_income = 0
            total_expense = 0
            category_expenses = {}
            transactions = []
            
            for record in filtered_records:
                try:
                    income = parse_amount(str(record.get('Pemasukan', ''))) or 0
                    expense = parse_amount(str(record.get('Pengeluaran', ''))) or 0
                    category = record.get('Kategori', 'Lainnya')
                    
                    total_income += income
                    total_expense += expense
                    
                    # Track category expenses
                    if expense > 0:
                        category_expenses[category] = category_expenses.get(category, 0) + expense
                    
                    # Add to transactions list
                    amount = income if income > 0 else -expense
                    transactions.append({
                        'date': record.get('Tanggal', ''),
                        'category': category,
                        'description': record.get('Deskripsi', ''),
                        'amount': amount
                    })
                    
                except (ValueError, KeyError):
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
            return {}
    
    async def search_transactions(self, user_id: int, query: str) -> List[Dict]:
        """Search transactions based on query"""
        try:
            if user_id not in self.user_sheets:
                return []
            
            spreadsheet = self.user_sheets[user_id]
            transactions_sheet = spreadsheet.worksheet('Transactions')
            records = transactions_sheet.get_all_records()
            
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
                        
                        income_val = parse_amount(income) or 0
                        expense_val = parse_amount(expense) or 0
                        amount = income_val if income_val > 0 else -expense_val
                        
                        results.append({
                            'date': record.get('Tanggal', ''),
                            'category': record.get('Kategori', ''),
                            'description': record.get('Deskripsi', ''),
                            'amount': amount
                        })
                        
                except (ValueError, KeyError):
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
            records = transactions_sheet.get_all_records()
            
            target_date = date.strftime('%Y-%m-%d')
            daily_transactions = []
            
            for record in records:
                if record.get('Tanggal') == target_date:
                    income = parse_amount(str(record.get('Pemasukan', ''))) or 0
                    expense = parse_amount(str(record.get('Pengeluaran', ''))) or 0
                    amount = income if income > 0 else -expense
                    
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
            categories_sheet = spreadsheet.worksheet('Categories')
            records = categories_sheet.get_all_records()
            
            return records
            
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
            return {}
    
    async def _update_monthly_summary(self, user_id: int, amount: float, 
                                    transaction_type: str, date: datetime):
        """Update monthly summary sheet"""
        try:
            spreadsheet = self.user_sheets[user_id]
            summary_sheet = spreadsheet.worksheet('Monthly_Summary')
            
            period_key = f"{date.year}-{date.month:02d}"
            
            # Get existing records
            records = summary_sheet.get_all_records()
            
            # Find existing record for this month
            existing_row = None
            for i, record in enumerate(records):
                if record.get('Periode') == period_key:
                    existing_row = i + 2  # +2 because of header row and 0-based index
                    break
            
            if existing_row:
                # Update existing record
                current_income = parse_amount(str(records[existing_row-2].get('Total Pemasukan', ''))) or 0
                current_expense = parse_amount(str(records[existing_row-2].get('Total Pengeluaran', ''))) or 0
                
                if transaction_type == 'income':
                    new_income = current_income + amount
                    new_expense = current_expense
                else:
                    new_income = current_income
                    new_expense = current_expense + amount
                
                new_balance = new_income - new_expense
                
                # Update the row
                summary_sheet.update(f'B{existing_row}:D{existing_row}', [[new_income, new_expense, new_balance]])
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
                record_date = datetime.strptime(record['Tanggal'], '%Y-%m-%d')
                
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
                        
            except ValueError:
                continue
        
        return filtered