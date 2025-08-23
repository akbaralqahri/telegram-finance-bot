"""
Helper functions for Finance Bot with Enhanced Date Parsing
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Tuple
import pytz

from config import Config

logger = logging.getLogger(__name__)

def parse_amount(amount_text: str) -> Optional[float]:
    """Parse amount from various text formats"""
    if not amount_text:
        return None
    
    # Clean the input
    amount_text = str(amount_text).strip().lower()
    
    # Remove currency symbols
    amount_text = re.sub(r'[rp$€£¥₹]', '', amount_text)
    
    try:
        # Pattern 1: Simple numbers with separators
        if re.match(r'^\d+([.,]\d{3})*([.,]\d{1,2})?$', amount_text):
            # Handle different decimal separators
            if ',' in amount_text and '.' in amount_text:
                if amount_text.rfind(',') > amount_text.rfind('.'):
                    amount_text = amount_text.replace('.', '').replace(',', '.')
                else:
                    amount_text = amount_text.replace(',', '')
            elif ',' in amount_text:
                parts = amount_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    amount_text = amount_text.replace(',', '.')
                else:
                    amount_text = amount_text.replace(',', '')
            
            return float(amount_text)
        
        # Pattern 2: Numbers with multipliers
        multiplier_pattern = r'(\d+(?:[.,]\d+)?)\s*([kjtrb]|juta|ribu|rb|thousand|million|k|m|t)'
        match = re.search(multiplier_pattern, amount_text)
        
        if match:
            number_part = match.group(1).replace(',', '.')
            multiplier = match.group(2)
            
            base_amount = float(number_part)
            
            if multiplier in ['k', 'ribu', 'rb', 'thousand']:
                return base_amount * 1000
            elif multiplier in ['juta', 'million', 'm']:
                return base_amount * 1000000
            elif multiplier in ['t', 'trillion']:
                return base_amount * 1000000000000
        
        # Pattern 3: Simple number
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

def parse_date_from_text(date_text: str) -> Optional[datetime]:
    """
    Enhanced date parsing from various text formats
    
    Supported formats:
    - Natural language: hari ini, kemarin, besok, lusa
    - Days: Senin, Selasa, Rabu, dst
    - Dates: 25/12/2024, 25-12-2024, 25 Des, 25 Desember
    - Shortcuts: tgl 15, tanggal 20
    - Relative: 3 hari lalu, seminggu lalu, 2 minggu lalu
    """
    if not date_text:
        return None
        
    try:
        date_text = date_text.strip().lower()
        today = datetime.now()
        
        # Natural language dates
        if date_text in ['hari ini', 'today', 'sekarang']:
            return today
        elif date_text in ['kemarin', 'yesterday']:
            return today - timedelta(days=1)
        elif date_text in ['besok', 'tomorrow']:
            return today + timedelta(days=1)
        elif date_text in ['lusa', 'day after tomorrow']:
            return today + timedelta(days=2)
        
        # Days of week (this week)
        days_map = {
            'senin': 0, 'monday': 0,
            'selasa': 1, 'tuesday': 1,
            'rabu': 2, 'wednesday': 2,
            'kamis': 3, 'thursday': 3,
            'jumat': 4, 'friday': 4,
            'sabtu': 5, 'saturday': 5,
            'minggu': 6, 'sunday': 6, 'ahad': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in date_text:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        # Relative dates
        relative_patterns = [
            (r'(\d+)\s*hari\s*lalu', lambda m: today - timedelta(days=int(m.group(1)))),
            (r'(\d+)\s*hari\s*yang\s*lalu', lambda m: today - timedelta(days=int(m.group(1)))),
            (r'seminggu\s*lalu', lambda m: today - timedelta(weeks=1)),
            (r'(\d+)\s*minggu\s*lalu', lambda m: today - timedelta(weeks=int(m.group(1)))),
            (r'(\d+)\s*bulan\s*lalu', lambda m: today - timedelta(days=int(m.group(1)) * 30)),
        ]
        
        for pattern, func in relative_patterns:
            match = re.search(pattern, date_text)
            if match:
                return func(match)
        
        # Shortcut formats: tgl 15, tanggal 20
        shortcut_patterns = [
            r'(?:tgl|tanggal)\s*(\d{1,2})',
            r'(?:pada\s*)?(?:tanggal\s*)?(\d{1,2})'
        ]
        
        for pattern in shortcut_patterns:
            match = re.search(pattern, date_text)
            if match:
                day = int(match.group(1))
                if 1 <= day <= 31:
                    try:
                        # Try this month first
                        result = today.replace(day=day)
                        if result < today:
                            # If the date is in the past, assume next month
                            if today.month == 12:
                                result = result.replace(year=today.year + 1, month=1)
                            else:
                                result = result.replace(month=today.month + 1)
                        return result
                    except ValueError:
                        # Invalid day for current month, try next month
                        try:
                            if today.month == 12:
                                return datetime(today.year + 1, 1, day)
                            else:
                                return datetime(today.year, today.month + 1, day)
                        except ValueError:
                            continue
        
        # Standard date formats
        date_formats = [
            '%Y-%m-%d',      # 2024-12-25
            '%d/%m/%Y',      # 25/12/2024
            '%d-%m-%Y',      # 25-12-2024
            '%d/%m/%y',      # 25/12/24
            '%d-%m-%y',      # 25-12-24
            '%d.%m.%Y',      # 25.12.2024
            '%d %m %Y',      # 25 12 2024
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        # Month names (Indonesian)
        month_names = {
            'januari': 1, 'jan': 1,
            'februari': 2, 'feb': 2,
            'maret': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'mei': 5,
            'juni': 6, 'jun': 6,
            'juli': 7, 'jul': 7,
            'agustus': 8, 'agu': 8, 'ags': 8,
            'september': 9, 'sep': 9,
            'oktober': 10, 'okt': 10,
            'november': 11, 'nov': 11,
            'desember': 12, 'des': 12
        }
        
        # Date with month names: 25 Desember, 25 Des 2024
        month_pattern = r'(\d{1,2})\s+([a-z]+)(?:\s+(\d{4}))?'
        match = re.search(month_pattern, date_text)
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3)) if match.group(3) else today.year
            
            if month_str in month_names:
                month = month_names[month_str]
                try:
                    result = datetime(year, month, day)
                    # If the date is in the past and no year specified, assume next year
                    if result < today and not match.group(3):
                        result = result.replace(year=today.year + 1)
                    return result
                except ValueError:
                    pass
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_text}': {e}")
        return None

def parse_transaction_text(text: str) -> Optional[Dict]:
    """
    Enhanced transaction parsing with date support
    
    Examples:
    - "Beli makan 25000" -> {'type': 'expense', 'amount': 25000, 'description': 'Beli makan', 'date': today}
    - "Gaji 5 juta kemarin" -> {'type': 'income', 'amount': 5000000, 'description': 'Gaji', 'date': yesterday}
    - "Bayar listrik 150rb tanggal 1" -> {'type': 'expense', 'amount': 150000, 'description': 'Bayar listrik', 'date': 1st of month}
    """
    try:
        text = text.strip()
        original_text = text
        
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
        
        # Extract date from text first
        transaction_date = None
        date_patterns = [
            r'\b(kemarin|yesterday)\b',
            r'\b(besok|tomorrow)\b', 
            r'\b(lusa)\b',
            r'\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu|ahad)\b',
            r'\b(?:tgl|tanggal)\s*(\d{1,2})\b',
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b',
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})\b',
            r'\b(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|jun|jul|agu|sep|okt|nov|des)\b',
            r'\b(\d+)\s*hari\s*(?:yang\s*)?lalu\b',
            r'\b(\d+)\s*minggu\s*(?:yang\s*)?lalu\b',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_text = match.group(0)
                parsed_date = parse_date_from_text(date_text)
                if parsed_date:
                    transaction_date = parsed_date
                    # Remove date from text
                    text = text.replace(match.group(0), ' ').strip()
                    text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                    break
            if transaction_date:
                break
        
        # Extract amount from remaining text
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
                        text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces
                        break
                if amount:
                    break
        
        if not amount:
            return None
        
        # Determine transaction type
        text_lower = text.lower()
        original_lower = original_text.lower()
        transaction_type = 'expense'  # Default to expense
        
        # Check for income keywords in both original and remaining text
        for keyword in income_keywords:
            if keyword in text_lower or keyword in original_lower:
                transaction_type = 'income'
                break
        
        # Clean up description
        description = text.strip()
        if not description:
            description = 'Transaksi' if transaction_type == 'expense' else 'Pemasukan'
        
        # Remove common connecting words
        description = re.sub(r'\b(pada|di|untuk|dari|ke|yang|adalah|dengan)\b', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Capitalize first letter
        description = description[0].upper() + description[1:] if description else 'Transaksi'
        
        result = {
            'type': transaction_type,
            'amount': amount,
            'description': description
        }
        
        # Add date if found
        if transaction_date:
            result['date'] = transaction_date
        
        return result
        
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
    """Validate and parse date string (legacy function, use parse_date_from_text instead)"""
    return parse_date_from_text(date_string)

def get_user_timezone(user_id: int = None) -> str:
    """Get user's timezone"""
    return Config.TIMEZONE

def convert_to_user_timezone(dt: datetime, user_id: int = None) -> datetime:
    """Convert datetime to user's timezone"""
    try:
        user_tz = get_user_timezone(user_id)
        timezone = pytz.timezone(user_tz)
        
        if dt.tzinfo is None:
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

def get_relative_date_text(date: datetime) -> str:
    """Get relative date text for display"""
    try:
        today = datetime.now().date()
        target_date = date.date()
        
        diff = (target_date - today).days
        
        if diff == 0:
            return "hari ini"
        elif diff == -1:
            return "kemarin"
        elif diff == 1:
            return "besok"
        elif diff == 2:
            return "lusa"
        elif -7 < diff < 0:
            return f"{abs(diff)} hari lalu"
        elif 0 < diff < 7:
            return f"{diff} hari lagi"
        else:
            return date.strftime('%d %B %Y')
            
    except Exception as e:
        logger.error(f"Error getting relative date text: {e}")
        return date.strftime('%d/%m/%Y')