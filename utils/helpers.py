"""
Helper functions for Finance Bot with Enhanced Date Parsing - CLEAN VERSION
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Tuple
import pytz

from config import Config

logger = logging.getLogger(__name__)

def parse_amount(amount_text: str) -> Optional[float]:
    """Parse amount from various text formats - FIXED VERSION"""
    if not amount_text:
        return None
    
    # Clean the input
    amount_text = str(amount_text).strip().lower()
    
    # Remove currency symbols
    amount_text = re.sub(r'[rp$€£¥₹]', '', amount_text)
    
    logger.debug(f"Parsing amount text: '{amount_text}'")
    
    try:
        # FIXED: Pattern for numbers with multipliers (prioritize this first)
        multiplier_pattern = r'(\d+(?:[.,]\d+)?)\s*([kjtrb]|ribu|rb|juta|jt|million|thousand|trillion|milyar)(?:\s|$)'
        match = re.search(multiplier_pattern, amount_text)
        
        if match:
            number_part = match.group(1).replace(',', '.')
            multiplier = match.group(2).lower().strip()
            
            logger.debug(f"Found multiplier pattern: number='{number_part}', multiplier='{multiplier}'")
            
            try:
                base_amount = float(number_part)
                
                # FIXED: More precise multiplier handling
                if multiplier in ['k', 'ribu', 'rb', 'thousand']:
                    result = base_amount * 1000
                    logger.debug(f"Applied thousands multiplier: {base_amount} * 1000 = {result}")
                    return result
                elif multiplier in ['juta', 'jt', 'million']:
                    result = base_amount * 1000000
                    logger.debug(f"Applied millions multiplier: {base_amount} * 1000000 = {result}")
                    return result
                elif multiplier in ['t', 'trillion']:
                    result = base_amount * 1000000000000
                    logger.debug(f"Applied trillions multiplier: {base_amount} * 1000000000000 = {result}")
                    return result
                elif multiplier in ['milyar']:
                    result = base_amount * 1000000000
                    logger.debug(f"Applied billions multiplier: {base_amount} * 1000000000 = {result}")
                    return result
                else:
                    logger.warning(f"Unknown multiplier: '{multiplier}', treating as base amount")
                    return base_amount
                    
            except ValueError as e:
                logger.error(f"Error parsing number part '{number_part}': {e}")
                pass
        
        # Pattern 1: Simple numbers with separators (check after multipliers)
        simple_number_pattern = r'^\d+([.,]\d{3})*([.,]\d{1,2})?$'
        if re.match(simple_number_pattern, amount_text):
            logger.debug(f"Processing as simple number with separators: '{amount_text}'")
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
            
            result = float(amount_text)
            logger.debug(f"Parsed as simple number: {result}")
            return result
        
        # Pattern 2: Simple number (fallback)
        number_match = re.search(r'(\d+(?:\.\d+)?)', amount_text)
        if number_match:
            result = float(number_match.group(1))
            logger.debug(f"Parsed as fallback simple number: {result}")
            return result
        
        logger.warning(f"No pattern matched for amount: '{amount_text}'")
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
        
        if currency and hasattr(Config, 'CURRENCY_SYMBOLS') and currency in Config.CURRENCY_SYMBOLS:
            currency_symbol = Config.CURRENCY_SYMBOLS[currency]
        
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
    """Enhanced date parsing from various text formats"""
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
        
        # Standard date formats
        date_formats = [
            '%d/%m/%Y',      # 22/08/2025
            '%d-%m-%Y',      # 22-08-2025
            '%d.%m.%Y',      # 22.08.2025
            '%Y-%m-%d',      # 2025-08-22
            '%d/%m/%y',      # 22/08/25
            '%d-%m-%y',      # 22-08-25
            '%d %m %Y',      # 22 08 2025
        ]
        
        # Try standard formats first
        original_date_text = date_text
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_text, fmt)
                logger.info(f"Successfully parsed '{original_date_text}' as {parsed_date.strftime('%Y-%m-%d')} using format {fmt}")
                return parsed_date
            except ValueError:
                continue
        
        # Month names (Indonesian)
        month_names = {
            'januari': 1, 'jan': 1,
            'februari': 2, 'feb': 2, 'peb': 2,
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
        
        # Date with month names patterns
        month_patterns = [
            r'(\d{1,2})\s+([a-z]+)(?:\s+(\d{4}))?',
            r'(\d{1,2})[\/\-]([a-z]+)[\/\-]?(\d{4})?',
            r'([a-z]+)\s+(\d{1,2})(?:\s+(\d{4}))?',
        ]
        
        for pattern in month_patterns:
            match = re.search(pattern, date_text)
            if match:
                groups = match.groups()
                
                if groups[0].isdigit():
                    day = int(groups[0])
                    month_str = groups[1]
                    year = int(groups[2]) if groups[2] else today.year
                else:
                    month_str = groups[0]
                    day = int(groups[1])
                    year = int(groups[2]) if groups[2] else today.year
                
                if month_str in month_names:
                    month = month_names[month_str]
                    try:
                        result = datetime(year, month, day)
                        logger.info(f"Successfully parsed '{original_date_text}' with month name as {result.strftime('%Y-%m-%d')}")
                        return result
                    except ValueError as ve:
                        logger.warning(f"Invalid date components: day={day}, month={month}, year={year}: {ve}")
                        continue
        
        # Days of week
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
                if days_ahead <= 0:
                    days_ahead += 7
                result = today + timedelta(days=days_ahead)
                logger.info(f"Successfully parsed '{original_date_text}' as day of week: {result.strftime('%Y-%m-%d')}")
                return result
        
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
                result = func(match)
                logger.info(f"Successfully parsed '{original_date_text}' as relative date: {result.strftime('%Y-%m-%d')}")
                return result
        
        # Shortcut formats: tgl 15, tanggal 20
        shortcut_patterns = [
            r'(?:tgl|tanggal)\s*(\d{1,2})',
            r'(?:pada\s*)?(?:tanggal\s*)?(\d{1,2})(?!\s*[\/\-]\s*\d)'
        ]
        
        for pattern in shortcut_patterns:
            match = re.search(pattern, date_text)
            if match:
                day = int(match.group(1))
                if 1 <= day <= 31:
                    try:
                        result = today.replace(day=day)
                        if result < today:
                            if today.month == 12:
                                result = result.replace(year=today.year + 1, month=1)
                            else:
                                result = result.replace(month=today.month + 1)
                        logger.info(f"Successfully parsed '{original_date_text}' as shortcut date: {result.strftime('%Y-%m-%d')}")
                        return result
                    except ValueError:
                        try:
                            if today.month == 12:
                                result = datetime(today.year + 1, 1, day)
                            else:
                                result = datetime(today.year, today.month + 1, day)
                            logger.info(f"Successfully parsed '{original_date_text}' as shortcut date (next month): {result.strftime('%Y-%m-%d')}")
                            return result
                        except ValueError:
                            continue
        
        logger.warning(f"Could not parse date: '{original_date_text}'")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_text}': {e}")
        return None

def parse_transaction_text(text: str) -> Optional[Dict]:
    """Enhanced transaction parsing with date support"""
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
            r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})\b',
            r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2})\b',
            r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b',
            r'\b(\d{1,2}\s+(?:januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|jun|jul|agu|sep|okt|nov|des)(?:\s+\d{4})?)\b',
            r'\b(kemarin|yesterday)\b',
            r'\b(besok|tomorrow)\b', 
            r'\b(lusa)\b',
            r'\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu|ahad)\b',
            r'\b(?:tgl|tanggal)\s*(\d{1,2})\b',
            r'\b(?:pada\s*)?(?:tanggal\s*)(\d{1,2})\b',
            r'\b(\d+)\s*hari\s*(?:yang\s*)?lalu\b',
            r'\b(\d+)\s*minggu\s*(?:yang\s*)?lalu\b',
        ]
        
        # Find and extract date
        date_match_found = False
        for pattern in date_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                date_text = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                parsed_date = parse_date_from_text(date_text)
                if parsed_date:
                    transaction_date = parsed_date
                    text = text[:match.start()] + ' ' + text[match.end():]
                    text = re.sub(r'\s+', ' ', text).strip()
                    date_match_found = True
                    logger.info(f"Extracted date '{date_text}' -> {parsed_date.strftime('%Y-%m-%d')} from transaction text")
                    break
            if date_match_found:
                break
        
        # Extract amount from remaining text
        amount = None
        amount_patterns = [
            r'(\d+(?:[.,]\d+)?\s*(?:rb|ribu|k|jt|juta|m|million|t|trillion|milyar|b))',
            r'(\d+(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            r'(\d+(?:\.\d+)?)'
        ]
        
        amount_match_found = False
        for pattern in amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_text = match.group(1)
                parsed_amount = parse_amount(amount_text)
                if parsed_amount and parsed_amount > 0:
                    amount = parsed_amount
                    text = text[:match.start()] + ' ' + text[match.end():]
                    text = re.sub(r'\s+', ' ', text).strip()
                    amount_match_found = True
                    logger.info(f"Extracted amount '{amount_text}' -> {amount} from transaction text")
                    break
            if amount_match_found:
                break
        
        if not amount:
            logger.warning(f"No valid amount found in transaction text: '{original_text}'")
            return None
        
        # Determine transaction type
        text_lower = text.lower()
        original_lower = original_text.lower()
        transaction_type = 'expense'
        
        for keyword in income_keywords:
            if keyword in text_lower or keyword in original_lower:
                transaction_type = 'income'
                break
        
        # Clean up description
        description = text.strip()
        if not description:
            description = 'Transaksi' if transaction_type == 'expense' else 'Pemasukan'
        
        # Remove common connecting words
        description = re.sub(r'\b(pada|di|untuk|dari|ke|yang|adalah|dengan|ditanggal|di tanggal|pd|tgl|tanggal)\b', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Capitalize first letter
        description = description[0].upper() + description[1:] if description else 'Transaksi'
        
        result = {
            'type': transaction_type,
            'amount': amount,
            'description': description
        }
        
        if transaction_date:
            result['date'] = transaction_date
            logger.info(f"Final parsed transaction: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing transaction text '{text}': {e}")
        return None

def detect_transaction_category(description: str, transaction_type: str) -> str:
    """Detect transaction category based on description"""
    try:
        description_lower = description.lower()
        
        categories = Config.DEFAULT_CATEGORIES.get(transaction_type, [])
        
        category_scores = {}
        
        for category in categories:
            score = 0
            for keyword in category['keywords']:
                if keyword.lower() in description_lower:
                    score += len(keyword) * 2
                    if f' {keyword.lower()} ' in f' {description_lower} ':
                        score += 5
        
            if score > 0:
                category_scores[category['name']] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            logger.info(f"Detected category '{best_category}' for '{description}'")
            return best_category
        
        return 'Lainnya'
        
    except Exception as e:
        logger.error(f"Error detecting category for '{description}': {e}")
        return 'Lainnya'

def validate_date(date_string: str) -> Optional[datetime]:
    """Validate and parse date string"""
    return parse_date_from_text(date_string)

def get_user_timezone(user_id: int = None) -> str:
    """Get user's timezone"""
    return getattr(Config, 'TIMEZONE', 'Asia/Jakarta')

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
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        filename = filename.strip('. ')
        
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