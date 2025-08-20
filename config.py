"""
Configuration file for Telegram Finance Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    # AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Google Sheets Configuration
    SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Finance Tracker')
    TEMPLATE_SHEET_ID = os.getenv('TEMPLATE_SHEET_ID')
    
    # Localization
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Jakarta')
    CURRENCY = os.getenv('CURRENCY', 'IDR')
    CURRENCY_SYMBOL = {
        'IDR': 'Rp',
        'USD': '$',
        'EUR': '€',
        'SGD': 'S$'
    }.get(os.getenv('CURRENCY', 'IDR'), 'Rp')
    
    # File Paths
    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.json'
    CATEGORIES_FILE = 'data/categories.json'
    
    # Google Sheets Headers
    TRANSACTION_HEADERS = [
        'Tanggal', 'Waktu', 'Kategori', 'Deskripsi', 
        'Pemasukan', 'Pengeluaran', 'Saldo', 'User ID'
    ]
    
    CATEGORY_HEADERS = [
        'Kategori', 'Type', 'Keywords', 'Icon'
    ]
    
    SUMMARY_HEADERS = [
        'Periode', 'Total Pemasukan', 'Total Pengeluaran', 
        'Saldo Akhir', 'User ID'
    ]
    
    # Default Categories
    DEFAULT_CATEGORIES = {
        'income': [
            {'name': 'Gaji', 'keywords': ['gaji', 'salary', 'upah'], 'icon': '💰'},
            {'name': 'Bonus', 'keywords': ['bonus', 'tunjangan'], 'icon': '🎁'},
            {'name': 'Investasi', 'keywords': ['dividen', 'bunga', 'profit'], 'icon': '📈'},
            {'name': 'Freelance', 'keywords': ['freelance', 'project', 'client'], 'icon': '💻'},
            {'name': 'Lainnya', 'keywords': ['lain', 'other', 'misc'], 'icon': '💵'}
        ],
        'expense': [
            {'name': 'Makanan', 'keywords': ['makan', 'food', 'groceries', 'restaurant', 'cafe'], 'icon': '🍽️'},
            {'name': 'Transport', 'keywords': ['bensin', 'fuel', 'grab', 'gojek', 'taxi', 'bus'], 'icon': '🚗'},
            {'name': 'Belanja', 'keywords': ['beli', 'shopping', 'market', 'mall'], 'icon': '🛒'},
            {'name': 'Tagihan', 'keywords': ['listrik', 'internet', 'air', 'telepon', 'wifi'], 'icon': '🧾'},
            {'name': 'Kesehatan', 'keywords': ['dokter', 'obat', 'hospital', 'medical'], 'icon': '🏥'},
            {'name': 'Hiburan', 'keywords': ['movie', 'game', 'concert', 'vacation'], 'icon': '🎬'},
            {'name': 'Pendidikan', 'keywords': ['kursus', 'buku', 'course', 'training'], 'icon': '📚'},
            {'name': 'Lainnya', 'keywords': ['lain', 'other', 'misc'], 'icon': '💸'}
        ]
    }
    
    # AI Prompts
    AI_SYSTEM_PROMPT = """
    Anda adalah asisten keuangan pribadi yang cerdas dan membantu. 
    Tugas Anda adalah membantu pengguna menganalisis keuangan mereka dan memberikan saran yang berguna.
    
    Kemampuan Anda:
    1. Menganalisis pola pengeluaran
    2. Memberikan tips hemat dan budgeting
    3. Menyarankan optimasi keuangan
    4. Membantu perencanaan keuangan
    5. Menjawab pertanyaan seputar keuangan
    
    Selalu berikan respons yang:
    - Praktis dan actionable
    - Sesuai dengan kondisi keuangan Indonesia
    - Ramah dan mudah dipahami
    - Tidak memberikan saran investasi spesifik
    """
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True