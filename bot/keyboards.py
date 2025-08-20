"""
Keyboard layouts for Telegram Finance Bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import Config

def get_main_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Tambah Pemasukan", callback_data="add_income"),
            InlineKeyboardButton("💸 Tambah Pengeluaran", callback_data="add_expense")
        ],
        [
            InlineKeyboardButton("📊 Laporan", callback_data="view_report"),
            InlineKeyboardButton("💵 Cek Saldo", callback_data="check_balance")
        ],
        [
            InlineKeyboardButton("🔍 Cari Transaksi", callback_data="search_transaction"),
            InlineKeyboardButton("🤖 AI Assistant", callback_data="ai_help")
        ],
        [
            InlineKeyboardButton("🏷️ Kategori", callback_data="view_categories"),
            InlineKeyboardButton("📚 Bantuan", callback_data="help")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_transaction_type_keyboard():
    """Get transaction type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Pemasukan", callback_data="type_income"),
            InlineKeyboardButton("💸 Pengeluaran", callback_data="type_expense")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_category_keyboard(transaction_type="expense"):
    """Get category selection keyboard"""
    categories = Config.DEFAULT_CATEGORIES.get(transaction_type, [])
    
    keyboard = []
    
    # Create rows of 2 buttons each
    for i in range(0, len(categories), 2):
        row = []
        for j in range(i, min(i + 2, len(categories))):
            cat = categories[j]
            button_text = f"{cat['icon']} {cat['name']}"
            callback_data = f"category_{cat['name']}"
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        keyboard.append(row)
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_report_keyboard():
    """Get report type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Hari Ini", callback_data="daily_report"),
            InlineKeyboardButton("📆 Minggu Ini", callback_data="weekly_report")
        ],
        [
            InlineKeyboardButton("🗓️ Bulan Ini", callback_data="monthly_report"),
            InlineKeyboardButton("📈 Tahun Ini", callback_data="yearly_report")
        ],
        [
            InlineKeyboardButton("📊 By Kategori", callback_data="category_report"),
            InlineKeyboardButton("📋 Export", callback_data="export_report")
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Get yes/no confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Tidak", callback_data="confirm_no")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_amount_quick_keyboard():
    """Get quick amount selection keyboard"""
    amounts = [
        ["10.000", "25.000", "50.000"],
        ["100.000", "250.000", "500.000"],
        ["1.000.000", "2.500.000", "5.000.000"]
    ]
    
    keyboard = []
    for row in amounts:
        button_row = []
        for amount in row:
            button_row.append(InlineKeyboardButton(amount, callback_data=f"amount_{amount}"))
        keyboard.append(button_row)
    
    # Add custom amount button
    keyboard.append([InlineKeyboardButton("✏️ Input Manual", callback_data="amount_custom")])
    
    return InlineKeyboardMarkup(keyboard)

def get_period_keyboard():
    """Get time period selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Hari Ini", callback_data="period_today"),
            InlineKeyboardButton("📅 Kemarin", callback_data="period_yesterday")
        ],
        [
            InlineKeyboardButton("📆 Minggu Ini", callback_data="period_this_week"),
            InlineKeyboardButton("📆 Minggu Lalu", callback_data="period_last_week")
        ],
        [
            InlineKeyboardButton("🗓️ Bulan Ini", callback_data="period_this_month"),
            InlineKeyboardButton("🗓️ Bulan Lalu", callback_data="period_last_month")
        ],
        [
            InlineKeyboardButton("📊 Tahun Ini", callback_data="period_this_year"),
            InlineKeyboardButton("✏️ Custom", callback_data="period_custom")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_search_type_keyboard():
    """Get search type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Berdasarkan Nominal", callback_data="search_amount"),
            InlineKeyboardButton("🏷️ Berdasarkan Kategori", callback_data="search_category")
        ],
        [
            InlineKeyboardButton("📝 Berdasarkan Deskripsi", callback_data="search_description"),
            InlineKeyboardButton("📅 Berdasarkan Tanggal", callback_data="search_date")
        ],
        [
            InlineKeyboardButton("🔍 Pencarian Bebas", callback_data="search_free"),
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_ai_suggestions_keyboard():
    """Get AI suggestion quick buttons"""
    suggestions = [
        "Analisis pengeluaran bulan ini",
        "Tips hemat untuk kategori makanan", 
        "Prediksi tabungan bulan depan",
        "Kategori mana yang paling boros?",
        "Saran budgeting untuk income saya"
    ]
    
    keyboard = []
    for suggestion in suggestions:
        # Truncate long suggestions for button text
        button_text = suggestion[:30] + "..." if len(suggestion) > 30 else suggestion
        callback_data = f"ai_suggestion_{suggestions.index(suggestion)}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add custom question button
    keyboard.append([InlineKeyboardButton("✏️ Pertanyaan Custom", callback_data="ai_custom")])
    
    return InlineKeyboardMarkup(keyboard)