"""
Keyboard layouts for Telegram Finance Bot with Date Picker
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
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

def get_date_keyboard():
    """Get date selection keyboard with quick options"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    # Get days of current week
    monday = today - timedelta(days=today.weekday())
    
    keyboard = [
        [
            InlineKeyboardButton("📅 Hari Ini", callback_data="date_hari ini"),
            InlineKeyboardButton("📅 Kemarin", callback_data="date_kemarin")
        ],
        [
            InlineKeyboardButton("📅 Besok", callback_data="date_besok"),
            InlineKeyboardButton("📅 Lusa", callback_data="date_lusa")
        ]
    ]
    
    # Add days of this week
    days_row = []
    day_names = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
    full_day_names = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
    
    for i, (short_name, full_name) in enumerate(zip(day_names, full_day_names)):
        day_date = monday + timedelta(days=i)
        if len(days_row) == 4:  # Max 4 buttons per row
            keyboard.append(days_row)
            days_row = []
        days_row.append(InlineKeyboardButton(short_name, callback_data=f"date_{full_name}"))
    
    if days_row:
        keyboard.append(days_row)
    
    # Add quick date shortcuts
    keyboard.extend([
        [
            InlineKeyboardButton("📅 Tgl 1", callback_data="date_tanggal 1"),
            InlineKeyboardButton("📅 Tgl 15", callback_data="date_tanggal 15"),
            InlineKeyboardButton("📅 Tgl 31", callback_data="date_tanggal 31")
        ],
        [
            InlineKeyboardButton("📝 Ketik Tanggal Manual", callback_data="date_manual"),
        ]
    ])
    
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
            InlineKeyboardButton("✅ Ya, Simpan", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Batal", callback_data="confirm_no")
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

def get_export_format_keyboard():
    """Get export format selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Excel (.xlsx)", callback_data="export_excel"),
            InlineKeyboardButton("📄 PDF", callback_data="export_pdf")
        ],
        [
            InlineKeyboardButton("📝 CSV", callback_data="export_csv"),
            InlineKeyboardButton("📋 Text", callback_data="export_text")
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_report")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Get settings menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💱 Ubah Currency", callback_data="setting_currency"),
            InlineKeyboardButton("🕐 Ubah Timezone", callback_data="setting_timezone")
        ],
        [
            InlineKeyboardButton("🏷️ Kelola Kategori", callback_data="setting_categories"),
            InlineKeyboardButton("🔔 Notifikasi", callback_data="setting_notifications")
        ],
        [
            InlineKeyboardButton("📊 Reset Data", callback_data="setting_reset"),
            InlineKeyboardButton("💾 Backup", callback_data="setting_backup")
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_currency_keyboard():
    """Get currency selection keyboard"""
    currencies = [
        ("🇮🇩 Rupiah (IDR)", "currency_IDR"),
        ("🇺🇸 Dollar (USD)", "currency_USD"),
        ("🇪🇺 Euro (EUR)", "currency_EUR"),
        ("🇸🇬 Singapore Dollar (SGD)", "currency_SGD")
    ]
    
    keyboard = []
    for name, callback in currencies:
        keyboard.append([InlineKeyboardButton(name, callback_data=callback)])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_to_settings")])
    
    return InlineKeyboardMarkup(keyboard)

def get_quick_reply_keyboard():
    """Get quick reply keyboard for common commands"""
    keyboard = [
        [KeyboardButton("💰 Pemasukan"), KeyboardButton("💸 Pengeluaran")],
        [KeyboardButton("📊 Laporan"), KeyboardButton("💵 Saldo")],
        [KeyboardButton("🤖 AI"), KeyboardButton("📚 Bantuan")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False,
        input_field_placeholder="Ketik transaksi atau pilih menu..."
    )

def get_admin_keyboard():
    """Get admin menu keyboard (for bot administrators)"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Stats Pengguna", callback_data="admin_user_stats"),
            InlineKeyboardButton("📈 Bot Analytics", callback_data="admin_analytics")
        ],
        [
            InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("💾 Backup All Data", callback_data="admin_backup"),
            InlineKeyboardButton("🗂️ Export Users", callback_data="admin_export")
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_date_range_keyboard():
    """Get date range selection keyboard for reports"""
    keyboard = [
        [
            InlineKeyboardButton("📅 7 Hari Terakhir", callback_data="range_7days"),
            InlineKeyboardButton("📅 30 Hari Terakhir", callback_data="range_30days")
        ],
        [
            InlineKeyboardButton("📆 3 Bulan Terakhir", callback_data="range_3months"),
            InlineKeyboardButton("📆 6 Bulan Terakhir", callback_data="range_6months")
        ],
        [
            InlineKeyboardButton("🗓️ 1 Tahun Terakhir", callback_data="range_1year"),
            InlineKeyboardButton("✏️ Custom Range", callback_data="range_custom")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_month_keyboard(year: int = None):
    """Get month selection keyboard"""
    if not year:
        year = datetime.now().year
    
    months = [
        ("Jan", 1), ("Feb", 2), ("Mar", 3), ("Apr", 4),
        ("Mei", 5), ("Jun", 6), ("Jul", 7), ("Agu", 8),
        ("Sep", 9), ("Okt", 10), ("Nov", 11), ("Des", 12)
    ]
    
    keyboard = []
    row = []
    
    for month_name, month_num in months:
        if len(row) == 3:  # 3 buttons per row
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(month_name, callback_data=f"month_{year}_{month_num}"))
    
    if row:
        keyboard.append(row)
    
    # Add navigation
    keyboard.append([
        InlineKeyboardButton(f"◀️ {year-1}", callback_data=f"year_{year-1}"),
        InlineKeyboardButton(f"{year+1} ▶️", callback_data=f"year_{year+1}")
    ])
    
    return InlineKeyboardMarkup(keyboard)