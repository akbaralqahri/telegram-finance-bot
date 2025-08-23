"""
Bot command handlers with PERSISTENT MENU support - COMPLETE VERSION
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, BotCommand
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import Config
from services.google_sheets import GoogleSheetsService
from services.gemini_ai import GeminiAIService
from utils.helpers import (
    parse_amount, parse_transaction_text, format_currency,
    get_user_timezone, validate_date, parse_date_from_text
)
from bot.keyboards import (
    get_main_keyboard, get_category_keyboard, get_report_keyboard,
    get_confirmation_keyboard, get_date_keyboard, get_persistent_keyboard,
    get_quick_action_keyboard, get_minimal_keyboard, get_bot_commands
)

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_AMOUNT = 1
WAITING_FOR_DESCRIPTION = 2
WAITING_FOR_DATE = 3
WAITING_FOR_CATEGORY = 4
WAITING_FOR_CONFIRMATION = 5

# Global services
sheets_service = GoogleSheetsService()
ai_service = GeminiAIService()

async def setup_bot_menu(application):
    """Setup persistent bot menu and commands"""
    try:
        # Set bot commands for menu
        commands = get_bot_commands()
        await application.bot.set_my_commands(commands)
        
        logger.info("✅ Bot commands setup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up bot menu: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with persistent menu"""
    user = update.effective_user
    
    try:
        # Initialize user's spreadsheet if not exists
        success = await sheets_service.initialize_user_sheet(user.id, user.first_name)
        
        if not success:
            await update.message.reply_text(
                "❌ Gagal menginisialisasi spreadsheet. Pastikan credentials.json sudah ada dan Google Sheets API sudah enabled."
            )
            return
        
        # Get user's current balance
        balance = await sheets_service.get_user_balance(user.id)
        balance_text = format_currency(balance)
        
        # Get this month's summary
        today = datetime.now()
        monthly_summary = await sheets_service.get_monthly_summary(user.id, today.year, today.month)
        
        income_text = format_currency(monthly_summary.get('income', 0))
        expense_text = format_currency(monthly_summary.get('expense', 0))
        
        welcome_message = f"""
🏦 *Finance Assistant Bot* 💰

Halo {user.first_name}! 👋

📊 *Dashboard Keuangan Anda:*
💵 Saldo: {balance_text}
📈 Pemasukan Bulan Ini: {income_text}
📉 Pengeluaran Bulan Ini: {expense_text}

💡 *Cara Cepat Catat Transaksi:*
• Ketik: "Beli makan 25rb"
• Ketik: "Gaji bulan ini 5jt"  
• Ketik: "Bayar listrik 150rb kemarin"
• Ketik: "Ngopi 15rb tanggal 22/08/2025"

🚀 *Menu persisten sudah aktif di bawah!*
Gunakan tombol di bawah chat atau ketik transaksi langsung.
"""
        
        # Send message with persistent keyboard
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()  # PERSISTENT MENU
        )
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat memulai. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 *Panduan Finance Bot*

🚀 *MENU PERSISTEN AKTIF!*
Menu di bawah chat selalu tersedia - tidak perlu scroll atau ketik /start lagi!

🔹 *Cara Input Transaksi Cepat:*
• "Beli groceries 150rb"
• "Gaji november 8.5jt"
• "Makan di restaurant 75rb kemarin"
• "Ngopi 15rb tanggal 22/08/2025"

🔹 *Format Nominal yang Diterima:*
• 150000, 150.000, 150,000
• 1.5jt, 1.5 juta, 150k, 150rb

🔹 *Format Tanggal yang Diterima:*
• *Natural:* hari ini, kemarin, besok, lusa
• *Hari:* Senin, Selasa, Rabu, dst
• *Tanggal:* 25/12/2024, 25-12-2024, 25 Des
• *Shortcut:* tgl 15, tanggal 20

🔹 *Tombol Menu Persisten:*
• 💰 - Tambah Pemasukan
• 💸 - Tambah Pengeluaran  
• 📊 - Lihat Laporan
• 💵 - Cek Saldo
• 🔍 - Cari Transaksi
• 🤖 - AI Assistant

💡 Menu selalu tersedia di bawah chat!
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()  # Keep persistent menu
    )

async def handle_persistent_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input from persistent menu buttons"""
    message_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        # Handle persistent menu button presses
        if message_text == "💰 Pemasukan" or message_text == "💰 +":
            await income_command(update, context)
        elif message_text == "💸 Pengeluaran" or message_text == "💸 -":
            await expense_command(update, context)
        elif message_text == "📊 Laporan" or message_text == "📊":
            await report_command(update, context)
        elif message_text == "💵 Saldo" or message_text == "💵":
            await balance_command(update, context)
        elif message_text == "🔍 Cari" or message_text == "🔍":
            await update.message.reply_text(
                "🔍 *Pencarian Transaksi*\n\n"
                "Contoh pencarian:\n"
                "• `/search makanan` - Cari kategori makanan\n"
                "• `/search 100000` - Cari nominal 100rb\n"
                "• `/search 2024-12-25` - Cari tanggal spesifik\n"
                "• `/search groceries` - Cari deskripsi groceries",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_persistent_keyboard()
            )
        elif message_text == "🤖 AI" or message_text == "🤖":
            await update.message.reply_text(
                "🤖 *AI Finance Assistant*\n\n"
                "Contoh pertanyaan:\n"
                "• `/ai analisis pengeluaran bulan ini`\n"
                "• `/ai tips hemat untuk makanan`\n"
                "• `/ai prediksi tabungan bulan depan`\n"
                "• `/ai kategori apa yang paling boros?`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_persistent_keyboard()
            )
        elif message_text == "📚 Help" or message_text == "❓":
            await help_command(update, context)
        elif message_text == "💰":
            await quick_income(update, context)
        elif message_text == "💸":
            await quick_expense(update, context)
        else:
            # Not a menu button, try to parse as transaction
            return False  # Let other handlers process
            
        return True  # Handled by persistent menu
        
    except Exception as e:
        logger.error(f"Error handling persistent menu: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )
        return True

async def quick_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick income entry"""
    await update.message.reply_text(
        "💰 *Tambah Pemasukan Cepat*\n\n"
        "Ketik dalam format: *jumlah deskripsi*\n"
        "Contoh: `5000000 Gaji bulanan`\n"
        "Atau: `2jt Bonus project`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()
    )

async def quick_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick expense entry"""
    await update.message.reply_text(
        "💸 *Tambah Pengeluaran Cepat*\n\n"
        "Ketik dalam format: *jumlah deskripsi*\n"
        "Contoh: `25000 Beli makan`\n"
        "Atau: `150rb Bayar listrik`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()
    )

async def income_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /income command - add income transaction"""
    message = update.message if update.message else update.callback_query.message
    
    await message.reply_text(
        "💰 *Tambah Pemasukan*\n\n"
        "💵 Masukkan jumlah pemasukan:\n"
        "Contoh: 5000000, 5jt, 5 juta",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()  # Keep persistent menu
    )
    context.user_data['transaction_type'] = 'income'
    return WAITING_FOR_AMOUNT

async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /expense command - add expense transaction"""
    message = update.message if update.message else update.callback_query.message
    
    await message.reply_text(
        "💸 *Tambah Pengeluaran*\n\n"
        "💵 Masukkan jumlah pengeluaran:\n"
        "Contoh: 150000, 150rb, 150 ribu",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()  # Keep persistent menu
    )
    context.user_data['transaction_type'] = 'expense'
    return WAITING_FOR_AMOUNT

async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process amount input"""
    amount = parse_amount(update.message.text)
    
    if not amount or amount <= 0:
        await update.message.reply_text(
            "❌ Format nominal tidak valid. Silakan masukkan angka yang benar.\n"
            "Contoh: 150000, 150rb, 1.5jt",
            reply_markup=get_persistent_keyboard()
        )
        return WAITING_FOR_AMOUNT
    
    context.user_data['amount'] = amount
    transaction_type = context.user_data.get('transaction_type', 'expense')
    type_icon = "💰" if transaction_type == 'income' else "💸"
    
    await update.message.reply_text(
        f"{type_icon} Jumlah: {format_currency(amount)}\n\n"
        "📝 Masukkan deskripsi transaksi:\n"
        "Contoh: Beli groceries, Gaji bulanan, Bayar listrik",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_persistent_keyboard()  # Keep persistent menu
    )
    
    return WAITING_FOR_DESCRIPTION

async def process_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process description input"""
    description = update.message.text.strip()
    
    if len(description) < 3:
        await update.message.reply_text(
            "❌ Deskripsi terlalu pendek. Minimal 3 karakter.",
            reply_markup=get_persistent_keyboard()
        )
        return WAITING_FOR_DESCRIPTION
    
    context.user_data['description'] = description
    transaction_type = context.user_data.get('transaction_type', 'expense')
    type_icon = "💰" if transaction_type == 'income' else "💸"
    
    await update.message.reply_text(
        f"{type_icon} Deskripsi: {description}\n\n"
        "🗓️ Pilih tanggal transaksi atau ketik tanggal custom:",
        reply_markup=get_date_keyboard()  # Use inline keyboard for dates
    )
    
    return WAITING_FOR_DATE

async def process_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process date input"""
    date_input = update.message.text.strip() if update.message else None
    
    # If from callback query, get the date
    if update.callback_query:
        date_input = update.callback_query.data.replace("date_", "")
    
    if not date_input:
        await update.message.reply_text(
            "❌ Input tanggal tidak valid.",
            reply_markup=get_persistent_keyboard()
        )
        return WAITING_FOR_DATE
    
    # Parse the date
    transaction_date = parse_date_from_text(date_input)
    
    if not transaction_date:
        await update.message.reply_text(
            "❌ Format tanggal tidak valid.\n\n"
            "Format yang diterima:\n"
            "• hari ini, kemarin, besok\n"
            "• Senin, Selasa, dst\n"
            "• 25/12/2024, 25-12-2024\n"
            "• tgl 15, tanggal 20",
            reply_markup=get_persistent_keyboard()
        )
        return WAITING_FOR_DATE
    
    # Check if date is not too far in the future
    max_future_date = datetime.now() + timedelta(days=365)
    if transaction_date > max_future_date:
        await update.message.reply_text(
            "❌ Tanggal terlalu jauh di masa depan (maksimal 1 tahun ke depan).",
            reply_markup=get_persistent_keyboard()
        )
        return WAITING_FOR_DATE
    
    context.user_data['transaction_date'] = transaction_date
    
    # Show confirmation
    await show_transaction_confirmation(update, context)
    return WAITING_FOR_CONFIRMATION

async def show_transaction_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction confirmation before saving"""
    user_data = context.user_data
    transaction_type = user_data.get('transaction_type', 'expense')
    amount = user_data.get('amount', 0)
    description = user_data.get('description', '')
    transaction_date = user_data.get('transaction_date', datetime.now())
    
    type_icon = "💰" if transaction_type == 'income' else "💸"
    type_text = "Pemasukan" if transaction_type == 'income' else "Pengeluaran"
    
    # Auto-detect category
    category = await sheets_service.detect_category(description, transaction_type)
    user_data['category'] = category
    
    # Format date for display
    today = datetime.now().date()
    transaction_date_only = transaction_date.date()
    
    if transaction_date_only == today:
        date_display = "Hari ini"
    elif transaction_date_only == (today - timedelta(days=1)):
        date_display = "Kemarin"
    elif transaction_date_only == (today + timedelta(days=1)):
        date_display = "Besok"
    elif transaction_date_only == (today + timedelta(days=2)):
        date_display = "Lusa"
    else:
        # Use Indonesian month names for better display
        month_names_id = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        month_name = month_names_id.get(transaction_date.month, transaction_date.strftime('%B'))
        date_display = f"{transaction_date.day} {month_name} {transaction_date.year}"
    
    confirmation_text = f"""
📋 *Konfirmasi Transaksi*

{type_icon} *Jenis:* {type_text}
💵 *Jumlah:* {format_currency(amount)}
📝 *Deskripsi:* {description}
🗓️ *Tanggal:* {date_display}
🏷️ *Kategori:* {category}

Apakah data sudah benar?
"""
    
    message = update.message if update.message else update.callback_query.message
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            confirmation_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirmation_keyboard()
        )
    else:
        await message.reply_text(
            confirmation_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirmation_keyboard()
        )

async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process confirmation response"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_yes":
        # Save transaction
        await save_transaction(update, context)
    elif query.data == "confirm_no":
        # Cancel transaction
        await query.edit_message_text(
            "❌ Transaksi dibatalkan.\n\n"
            "Gunakan menu di bawah untuk mencoba lagi."
        )
        # Send new message with persistent keyboard
        await query.message.reply_text(
            "💡 Menu persisten tetap tersedia di bawah:",
            reply_markup=get_persistent_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    return ConversationHandler.END

async def save_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save transaction to spreadsheet"""
    user_data = context.user_data
    user_id = update.effective_user.id
    
    try:
        success = await sheets_service.add_transaction_with_date(
            user_id=user_id,
            amount=user_data.get('amount'),
            description=user_data.get('description'),
            category=user_data.get('category'),
            transaction_type=user_data.get('transaction_type'),
            transaction_date=user_data.get('transaction_date', datetime.now())
        )
        
        if success:
            type_icon = "💰" if user_data['transaction_type'] == 'income' else "💸"
            transaction_date = user_data.get('transaction_date', datetime.now())
            
            # Format date for display
            today = datetime.now().date()
            transaction_date_only = transaction_date.date()
            
            if transaction_date_only == today:
                date_display = ""
            elif transaction_date_only == (today - timedelta(days=1)):
                date_display = " (kemarin)"
            elif transaction_date_only == (today + timedelta(days=1)):
                date_display = " (besok)"
            elif transaction_date_only == (today + timedelta(days=2)):
                date_display = " (lusa)"
            else:
                month_names_id = {
                    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                    5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
                    9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
                }
                month_name = month_names_id.get(transaction_date.month, transaction_date.strftime('%b'))
                date_display = f" ({transaction_date.day} {month_name} {transaction_date.year})"
            
            actual_date_display = transaction_date.strftime('%d/%m/%Y')
            
            success_message = f"""
✅ *Transaksi berhasil dicatat!*

{type_icon} *{user_data['transaction_type'].title()}:* {format_currency(user_data['amount'])}
📝 *Deskripsi:* {user_data['description']}
🗓️ *Tanggal:* {actual_date_display}{date_display}
🏷️ *Kategori:* {user_data['category']}

💡 Gunakan menu di bawah untuk transaksi berikutnya.
"""
            
            await update.callback_query.edit_message_text(success_message, parse_mode=ParseMode.MARKDOWN)
            
            # Send new message with persistent keyboard to maintain menu
            await update.callback_query.message.reply_text(
                "🚀 Menu persisten siap digunakan:",
                reply_markup=get_persistent_keyboard()
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ Gagal menyimpan transaksi. Silakan coba lagi.",
                reply_markup=get_persistent_keyboard()
            )
            
        # Clear user data
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"Error saving transaction: {e}")
        await update.callback_query.edit_message_text(
            "❌ Terjadi kesalahan saat menyimpan.",
            reply_markup=get_persistent_keyboard()
        )

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - show financial reports"""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    report_type = 'monthly'
    if context.args:
        arg = context.args[0].lower()
        if arg in ['daily', 'weekly', 'monthly']:
            report_type = arg
    
    try:
        report_data = await sheets_service.generate_report(user_id, report_type)
        
        if report_type == 'daily':
            title = "📊 Laporan Harian"
            period = datetime.now().strftime("%d %B %Y")
        elif report_type == 'weekly':
            title = "📊 Laporan Mingguan"
            start_week = datetime.now() - timedelta(days=datetime.now().weekday())
            end_week = start_week + timedelta(days=6)
            period = f"{start_week.strftime('%d %b')} - {end_week.strftime('%d %b %Y')}"
        else:
            title = "📊 Laporan Bulanan"
            period = datetime.now().strftime("%B %Y")
        
        # Format report
        report_text = f"""
{title}
*Periode: {period}*

💰 *Total Pemasukan:* {format_currency(report_data.get('total_income', 0))}
💸 *Total Pengeluaran:* {format_currency(report_data.get('total_expense', 0))}
📊 *Net:* {format_currency(report_data.get('net_amount', 0))}
💵 *Saldo Saat Ini:* {format_currency(report_data.get('current_balance', 0))}

📈 *Top 5 Kategori Pengeluaran:*
"""
        
        top_expenses = report_data.get('top_expenses', [])
        if top_expenses:
            for i, (category, amount) in enumerate(top_expenses[:5], 1):
                report_text += f"{i}. {category}: {format_currency(amount)}\n"
        else:
            report_text += "Belum ada data pengeluaran\n"
        
        transactions = report_data.get('transactions', [])
        if transactions:
            report_text += f"\n📝 *Transaksi Terakhir:*\n"
            for trans in transactions[-5:]:
                date = trans.get('date', '')
                desc = trans.get('description', '')[:30]
                amount = format_currency(abs(trans.get('amount', 0)))
                type_icon = "💰" if trans.get('amount', 0) > 0 else "💸"
                report_text += f"• {date} {type_icon} {desc}: {amount}\n"
        else:
            report_text += "\n📝 *Transaksi Terakhir:*\nBelum ada transaksi\n"
        
        await message.reply_text(
            report_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()  # Keep persistent menu
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await message.reply_text(
            "❌ Gagal membuat laporan. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - search transactions"""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    if not context.args:
        await message.reply_text(
            "🔍 *Pencarian Transaksi*\n\n"
            "Contoh pencarian:\n"
            "• `/search makanan` - Cari kategori makanan\n"
            "• `/search 100000` - Cari nominal 100rb\n"
            "• `/search 2024-12-25` - Cari tanggal spesifik\n"
            "• `/search groceries` - Cari deskripsi groceries",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()
        )
        return
    
    search_query = ' '.join(context.args)
    
    try:
        results = await sheets_service.search_transactions(user_id, search_query)
        
        if not results:
            await message.reply_text(
                f"🔍 Tidak ditemukan transaksi untuk: *{search_query}*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_persistent_keyboard()
            )
            return
        
        # Format search results
        result_text = f"🔍 *Hasil Pencarian: {search_query}*\n\n"
        
        for trans in results[:10]:  # Limit to 10 results
            date = trans.get('date', '')
            category = trans.get('category', '')
            desc = trans.get('description', '')
            amount = format_currency(abs(trans.get('amount', 0)))
            type_icon = "💰" if trans.get('amount', 0) > 0 else "💸"
            
            result_text += f"📅 {date}\n"
            result_text += f"{type_icon} {category}: {desc}\n"
            result_text += f"💵 {amount}\n\n"
        
        if len(results) > 10:
            result_text += f"... dan {len(results) - 10} transaksi lainnya"
        
        await message.reply_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error searching transactions: {e}")
        await message.reply_text(
            "❌ Gagal mencari transaksi. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai command - AI assistant"""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    if not context.args:
        await message.reply_text(
            "🤖 *AI Finance Assistant*\n\n"
            "Contoh pertanyaan:\n"
            "• `/ai analisis pengeluaran bulan ini`\n"
            "• `/ai tips hemat untuk makanan`\n"
            "• `/ai prediksi tabungan bulan depan`\n"
            "• `/ai kategori apa yang paling boros?`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()
        )
        return
    
    user_question = ' '.join(context.args)
    
    # Send typing indicator
    await message.reply_chat_action("typing")
    
    try:
        # Get user's financial data for context
        financial_data = await sheets_service.get_user_financial_summary(user_id)
        
        # Get AI response
        ai_response = await ai_service.get_financial_advice(user_question, financial_data)
        
        await message.reply_text(
            f"🤖 *AI Assistant:*\n\n{ai_response}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in AI command: {e}")
        await message.reply_text(
            "❌ AI sedang tidak tersedia. Silakan coba lagi nanti.",
            reply_markup=get_persistent_keyboard()
        )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - show current balance"""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    try:
        balance = await sheets_service.get_user_balance(user_id)
        
        # Get today's transactions
        today_transactions = await sheets_service.get_daily_transactions(user_id)
        today_income = sum(t.get('amount', 0) for t in today_transactions if t.get('amount', 0) > 0)
        today_expense = sum(abs(t.get('amount', 0)) for t in today_transactions if t.get('amount', 0) < 0)
        
        balance_text = f"""
💰 *Saldo Saat Ini:* {format_currency(balance)}

📊 *Transaksi Hari Ini:*
💵 Pemasukan: {format_currency(today_income)}
💸 Pengeluaran: {format_currency(today_expense)}
📈 Net: {format_currency(today_income - today_expense)}

💡 Gunakan menu di bawah untuk aksi berikutnya
"""
        
        await message.reply_text(
            balance_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()  # Keep persistent menu
        )
        
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        await message.reply_text(
            "❌ Gagal mengambil saldo. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /categories command - manage categories"""
    message = update.message if update.message else update.callback_query.message
    
    try:
        categories = await sheets_service.get_user_categories(update.effective_user.id)
        
        if not categories:
            # Show default categories from config
            category_text = """
🏷️ *Kategori Default:*

💰 *Kategori Pemasukan:*
"""
            for cat in Config.DEFAULT_CATEGORIES.get('income', []):
                category_text += f"• {cat['icon']} {cat['name']}\n"
            
            category_text += "\n💸 *Kategori Pengeluaran:*\n"
            for cat in Config.DEFAULT_CATEGORIES.get('expense', []):
                category_text += f"• {cat['icon']} {cat['name']}\n"
        else:
            income_cats = [cat for cat in categories if cat.get('Type') == 'income']
            expense_cats = [cat for cat in categories if cat.get('Type') == 'expense']
            
            category_text = """
🏷️ *Kategori Pemasukan:*
"""
            for cat in income_cats:
                category_text += f"• {cat.get('Icon', '💰')} {cat.get('Kategori', 'Unknown')}\n"
            
            category_text += "\n💸 *Kategori Pengeluaran:*\n"
            for cat in expense_cats:
                category_text += f"• {cat.get('Icon', '💸')} {cat.get('Kategori', 'Unknown')}\n"
        
        category_text += "\n💡 Bot akan otomatis menentukan kategori berdasarkan deskripsi transaksi Anda."
        
        await message.reply_text(
            category_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_persistent_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing categories: {e}")
        await message.reply_text(
            "❌ Gagal menampilkan kategori. Silakan coba lagi.",
            reply_markup=get_persistent_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages with persistent menu support"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # First, check if it's a persistent menu button
    menu_handled = await handle_persistent_menu(update, context)
    if menu_handled:
        return
    
    # Try to parse as transaction with date
    transaction_data = parse_transaction_text(message_text)
    
    if transaction_data:
        try:
            # Auto-detect category
            category = await sheets_service.detect_category(
                transaction_data['description'], 
                transaction_data['type']
            )
            
            # Get transaction date (could be parsed from text or default to today)
            transaction_date = transaction_data.get('date', datetime.now())
            
            # Add transaction with custom date
            success = await sheets_service.add_transaction_with_date(
                user_id=user_id,
                amount=transaction_data['amount'],
                description=transaction_data['description'],
                category=category,
                transaction_type=transaction_data['type'],
                transaction_date=transaction_date
            )
            
            if success:
                type_icon = "💰" if transaction_data['type'] == 'income' else "💸"
                
                # Format date for display
                today = datetime.now().date()
                transaction_date_only = transaction_date.date()
                
                if transaction_date_only == today:
                    date_display = ""
                elif transaction_date_only == (today - timedelta(days=1)):
                    date_display = " (kemarin)"
                elif transaction_date_only == (today + timedelta(days=1)):
                    date_display = " (besok)"
                elif transaction_date_only == (today + timedelta(days=2)):
                    date_display = " (lusa)"
                else:
                    month_names_id = {
                        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                        5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
                        9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
                    }
                    month_name = month_names_id.get(transaction_date.month, transaction_date.strftime('%b'))
                    date_display = f" ({transaction_date.day} {month_name} {transaction_date.year})"
                
                # Show the actual date that was saved to database in the success message
                actual_date_display = transaction_date.strftime('%d/%m/%Y')
                
                await update.message.reply_text(
                    f"✅ Transaksi berhasil dicatat!\n\n"
                    f"{type_icon} *{transaction_data['type'].title()}:* {format_currency(transaction_data['amount'])}\n"
                    f"📝 *Deskripsi:* {transaction_data['description']}\n"
                    f"🗓️ *Tanggal:* {actual_date_display}{date_display}\n"
                    f"🏷️ *Kategori:* {category}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_persistent_keyboard()  # Keep persistent menu
                )
            else:
                await update.message.reply_text(
                    "❌ Gagal menyimpan transaksi. Silakan coba lagi.",
                    reply_markup=get_persistent_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            await update.message.reply_text(
                "❌ Gagal memproses transaksi. Silakan coba lagi.",
                reply_markup=get_persistent_keyboard()
            )
    else:
        # If not a transaction, maybe it's a question for AI
        if len(message_text) > 10 and any(word in message_text.lower() for word in 
                                         ['analisis', 'tips', 'saran', 'bagaimana', 'kapan', 'berapa']):
            await update.message.reply_text(
                f"🤖 Untuk pertanyaan AI, gunakan: `/ai {message_text}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_persistent_keyboard()
            )
        else:
            await update.message.reply_text(
                "❓ Saya tidak mengerti pesan Anda.\n\n"
                "💡 Contoh yang bisa saya pahami:\n"
                "• Beli makan 25rb\n"
                "• Gaji bulan ini 5 juta\n"
                "• Bayar listrik 150rb kemarin\n"
                "• Ngopi 15rb tanggal 22/08/2025\n\n"
                "🚀 Atau gunakan menu persisten di bawah!",
                reply_markup=get_persistent_keyboard()
            )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    try:
        if data == "add_income":
            await income_command(update, context)
        elif data == "add_expense":
            await expense_command(update, context)
        elif data == "view_report":
            await report_command(update, context)
        elif data == "daily_report":
            context.args = ['daily']
            await report_command(update, context)
        elif data == "weekly_report":
            context.args = ['weekly']
            await report_command(update, context)
        elif data == "monthly_report":
            context.args = ['monthly']
            await report_command(update, context)
        elif data == "check_balance":
            await balance_command(update, context)
        elif data == "ai_help":
            await ai_command(update, context)
        elif data == "view_categories":
            await categories_command(update, context)
        elif data == "help":
            await help_command(update, context)
        elif data.startswith("date_"):
            await process_date(update, context)
        elif data in ["confirm_yes", "confirm_no"]:
            await process_confirmation(update, context)
        else:
            await query.edit_message_text("❓ Pilihan tidak dikenali. Silakan gunakan /start untuk menu utama.")
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        try:
            await query.edit_message_text(
                "❌ Terjadi kesalahan. Silakan coba lagi atau gunakan /start untuk menu utama."
            )
        except Exception:
            pass

# Conversation handler setup
def get_conversation_handler():
    """Get the conversation handler for step-by-step transaction input"""
    from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CommandHandler('income', income_command),
            CommandHandler('expense', expense_command),
            CallbackQueryHandler(lambda u, c: income_command(u, c), pattern="^add_income$"),
            CallbackQueryHandler(lambda u, c: expense_command(u, c), pattern="^add_expense$")
        ],
        states={
            WAITING_FOR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount)],
            WAITING_FOR_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_description)],
            WAITING_FOR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_date),
                CallbackQueryHandler(process_date, pattern="^date_")
            ],
            WAITING_FOR_CONFIRMATION: [CallbackQueryHandler(process_confirmation, pattern="^confirm_")]
        },
        fallbacks=[
            CommandHandler('cancel', lambda u, c: ConversationHandler.END),
            CommandHandler('start', start_command)
        ],
        per_message=False
    )