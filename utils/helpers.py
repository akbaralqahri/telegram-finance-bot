"""
Helper functions for Finance Bot
Contains utility functions for parsing, formatting, and data processing
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Tuple
import pytz

from config import Config

logger = logging.getLogger(__name__)

def parse_amount(amount_text: str) -> Optional[float]:
    """
    Parse amount from various text formats
    
    Supported formats:
    - 150000, 150.000, 150,000
    - 1.5k, 1.5jt, 1.5 juta
    - 150rb, 150 ribu
    """
    if not amount_text:
        return None
    
    # Clean the input
    amount_text = str(amount_text).strip().lower()
    
    # Remove currency symbols
    amount_text = re.sub(r'[rp$€£¥₹]', '', amount_text)
    
    try:
        # Pattern 1: Simple numbers with separators (1.000.000,50 or 1,000,000.50)
        if re.match(r'^\d+([.,]\d{3})*([.,]\d{1,2})?$', amount_text):
            # Handle different decimal separators
            if ',' in amount_text and '.' in amount_text:
                # Determine which is decimal separator
                if amount_text.rfind(',') > amount_text.rfind('.'):
                    # Comma is decimal separator (European style)
                    amount_text = amount_text.replace('.', '').replace(',', '.')
                else:
                    # Dot is decimal separator (US style)
                    amount_text = amount_text.replace(',', '')
            elif ',' in amount_text:
                # Check if comma is thousand separator or decimal
                parts = amount_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Decimal separator
                    amount_text = amount_text.replace(',', '.')
                else:
                    # Thousand separator
                    amount_text = amount_text.replace(',', '')
            
            return float(amount_text)
        
        # Pattern 2: Numbers with multipliers (1.5k, 2jt, etc.)
        multiplier_pattern = r'(\d+(?:[.,]\d+)?)\s*([kjtrb]|juta|ribu|rb|thousand|million|k|m|t)'
        match = re.search(multiplier_pattern, amount_text)
        
        if match:
            number_part = match.group(1).replace(',', '.')
            multiplier = match.group(2)
            
            base_amount = float(number_part)
            
            # Apply multipliers
            if multiplier in ['k', 'ribu', 'rb', 'thousand']:
                return base_amount * 1000
            elif multiplier in ['juta', 'million', 'm']:
                return base_amount * 1000000
            elif multiplier in ['t', 'trillion']:
                return base_amount * 1000000000000
            
        # Pattern 3: Simple number without separators
        number_match = re.search(r'(\d+(?:\.\d+)?)', amount_text)
        if number_match:
            return float(number_match.group(1))
        
        return None
        
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse amount '{amount_text}': {e}")
        return None

def format_currency(amount: Union[float, int], currency: str = None) -> str:
    """Format amount as currency string"""
    try:
        if amount is None:
            return f"{Config.CURRENCY_SYMBOL} 0"
        
        amount = float(amount)
        currency_symbol = Config.CURRENCY_SYMBOL
        
        if currency and currency in Config.CURRENCY_SYMBOL:
            currency_symbol = Config.CURRENCY_SYMBOL[currency]
        
        # Format with thousand separators
        if amount >= 1000000000:  # Billions
            formatted = f"{amount/1000000000:.1f}M"
        elif amount >= 1000000:  # Millions
            formatted = f"{amount/1000000:.1f}jt"
        elif amount >= 1000:  # Thousands
            formatted = f"{amount/1000:.0f}rb" if amount < 10000 else f"{amount:,.0f}"
        else:
            formatted = f"{amount:,.0f}"
        
        # Use Indonesian number formatting (dot as thousand separator)
        if ',' in formatted:
            formatted = formatted.replace(',', '.')
        
        return f"{currency_symbol} {formatted}"
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting currency: {e}")
        return f"{Config.CURRENCY_SYMBOL} 0"

def parse_transaction_text(text: str) -> Optional[Dict]:
    """
    Parse natural language transaction text
    
    Examples:
    - "Beli makan 25000" -> {'type': 'expense', 'amount': 25000, 'description': 'Beli makan'}
    - "Gaji bulan ini 5 juta" -> {'type': 'income', 'amount': 5000000, 'description': 'Gaji bulan ini'}
    """
    try:
        text = text.strip()
        
        # Income keywords
        income_keywords = [
            'gaji', 'salary', 'upah', 'bonus', 'tunjangan', 'terima', 'dapat',
            'pendapatan', 'pemasukan', 'income', 'transfer masuk', 'dividen',
            'bunga', 'profit', 'keuntungan', 'freelance', 'project fee'
        ]
        
        # Expense keywords  
        expense_keywords = [
            'beli', 'bayar', 'buat', 'untuk', 'spend', 'expense', 'keluar',
            'shopping', 'belanja', 'makan', 'transport', 'bensin', 'listrik',
            'internet', 'tagihan', 'cicilan', 'top up', 'isi ulang'
        ]
        
        # Try to extract amount from text
        amount = None
        amount_patterns = [
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # Numbers with separators
            r'(\d+(?:[.,]\d+)?\s*(?:juta|jt|ribu|rb|k|thousand|million))',  # With multipliers
            r'(\d+)'  # Simple numbers
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    parsed_amount = parse_amount(match)
                    if parsed_amount and parsed_amount > 0:
                        amount = parsed_amount
                        # Remove amount from text to get description
                        text = re.sub(re.escape(match), '', text, 1).strip()
                        break
                if amount:
                    break
        
        if not amount:
            return None
        
        # Determine transaction type
        text_lower = text.lower()
        transaction_type = 'expense'  # Default to expense
        
        # Check for income keywords
        for keyword in income_keywords:
            if keyword in text_lower:
                transaction_type = 'income'
                break
        
        # Clean up description
        description = text.strip()
        if not description:
            description = 'Transaksi' if transaction_type == 'expense' else 'Pemasukan'
        
        # Capitalize first letter
        description = description[0].upper() + description[1:] if description else 'Transaksi'
        
        return {
            'type': transaction_type,
            'amount': amount,
            'description': description
        }
        
    except Exception as e:
        logger.error(f"Error parsing transaction text '{text}': {e}")
        return None

def detect_transaction_category(description: str, transaction_type: str) -> str:
    """Detect transaction category based on description"""
    try:
        description_lower = description.lower()
        
        # Get categories from config
        categories = Config.DEFAULT_CATEGORIES.get(transaction_type, [])
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category in categories:
            score = 0
            for keyword in category['keywords']:
                if keyword.lower() in description_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword) * 2
                    # Exact word match gets higher score
                    if f' {keyword.lower()} ' in f' {description_lower} ':
                        score += 5
        
            if score > 0:
                category_scores[category['name']] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            logger.info(f"Detected category '{best_category}' for '{description}'")
            return best_category
        
        # Default fallback
        return 'Lainnya'
        
    except Exception as e:
        logger.error(f"Error detecting category for '{description}': {e}")
        return 'Lainnya'

def validate_date(date_string: str) -> Optional[datetime]:
    """Validate and parse date string"""
    try:
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%d-%m-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # Natural language dates
        today = datetime.now()
        date_lower = date_string.lower().strip()
        
        if date_lower in ['hari ini', 'today']:
            return today
        elif date_lower in ['kemarin', 'yesterday']:
            return today - timedelta(days=1)
        elif date_lower in ['besok', 'tomorrow']:
            return today + timedelta(days=1)
        elif date_lower in ['lusa']:
            return today + timedelta(days=2)
        
        # Days of week
        days_map = {
            'senin': 0, 'monday': 0,
            'selasa': 1, 'tuesday': 1,
            'rabu': 2, 'wednesday': 2,
            'kamis': 3, 'thursday': 3,
            'jumat': 4, 'friday': 4,
            'sabtu': 5, 'saturday': 5,
            'minggu': 6, 'sunday': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in date_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        return None
        
    except Exception as e:
        logger.error(f"Error validating date '{date_string}': {e}")
        return None

def get_user_timezone(user_id: int = None) -> str:
    """Get user's timezone (can be expanded to store per-user preferences)"""
    # For now, return default timezone from config
    # In the future, this could query user preferences from database
    return Config.TIMEZONE

def convert_to_user_timezone(dt: datetime, user_id: int = None) -> datetime:
    """Convert datetime to user's timezone"""
    try:
        user_tz = get_user_timezone(user_id)
        timezone = pytz.timezone(user_tz)
        
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)
        
        return dt.astimezone(timezone)
        
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        return dt

def format_date(dt: datetime, format_type: str = 'short') -> str:
    """Format date for display"""
    try:
        if format_type == 'short':
            return dt.strftime('%d/%m/%Y')
        elif format_type == 'long':
            return dt.strftime('%d %B %Y')
        elif format_type == 'datetime':
            return dt.strftime('%d/%m/%Y %H:%M')
        else:
            return dt.strftime('%Y-%m-%d')
            
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return str(dt)

def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    try:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        
        return ((current - previous) / abs(previous)) * 100
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    try:
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or 'untitled'
        
    except Exception as e:
        logger.error(f"Error sanitizing filename: {e}")
        return 'untitled'

def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    import uuid
    return str(uuid.uuid4())[:8]

def validate_amount_range(amount: float, min_amount: float = 0.01, max_amount: float = 1000000000) -> bool:
    """Validate if amount is within acceptable range"""
    try:
        return min_amount <= amount <= max_amount
    except (TypeError, ValueError):
        return False