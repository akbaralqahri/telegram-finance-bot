"""
Bot command handlers for Telegram Finance Bot
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import Config
from services.google_sheets import GoogleSheetsService
from services.gemini_ai import GeminiAIService
from utils.helpers import (
    parse_amount, parse_transaction_text, format_currency,
    get_user_timezone, validate_date
)
from bot.keyboards import (
    get_main_keyboard, get_category_keyboard, get_report_keyboard,
    get_confirmation_keyboard
)

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_AMOUNT = 1
WAITING_FOR_DESCRIPTION = 2
WAITING_FOR_CATEGORY = 3
WAITING_FOR_DATE = 4

# Global services (will be initialized per user)
sheets_service = GoogleSheetsService()
ai_service = GeminiAIService()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
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
• Ketik: "Beli makan 25000"
• Ketik: "Gaji bulan ini 5 juta"
• Ketik: "Bayar listrik 150rb"

Atau gunakan menu di bawah ini:
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat memulai. Silakan coba lagi."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 *Panduan Finance Bot*

🔹 *Cara Input Transaksi Cepat:*
• "Beli groceries 150000"
• "Gaji november 8500000" 
• "Makan di restaurant 75000"
• "Bayar internet 350000"

🔹 *Format Nominal yang Diterima:*
• 150000, 150.000, 150,000
• 1.5jt, 1.5 juta, 150k, 150rb

🔹 *Perintah Tersedia:*
• `/income` - Tambah pemasukan
• `/expense` - Tambah pengeluaran  
• `/report` - Lihat laporan
• `/search` - Cari transaksi
• `/balance` - Cek saldo
• `/ai [pesan]` - Chat dengan AI
• `/categories` - Kelola kategori

🔹 *Contoh Chat AI:*
• `/ai analisis pengeluaran bulan ini`
• `/ai tips hemat untuk makanan`
• `/ai prediksi tabungan bulan depan`

🔹 *Laporan Tersedia:*
• Harian, Mingguan, Bulanan
• Berdasarkan kategori

❓ Butuh bantuan? Ketik /start untuk menu utama
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def income_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /income command - add income transaction"""
    user_id = update.effective_user.id
    
    # Determine message object (could be from command or callback)
    message = update.message if update.message else update.callback_query.message
    
    # Check if amount is provided in command
    if context.args:
        amount_text = ' '.join(context.args)
        amount = parse_amount(amount_text)
        
        if amount:
            # Store in context for next step
            context.user_data['transaction_type'] = 'income'
            context.user_data['amount'] = amount
            
            await message.reply_text(
                f"💰 Pemasukan: {format_currency(amount)}\n\n"
                "📝 Masukkan deskripsi pemasukan:"
            )
            return WAITING_FOR_DESCRIPTION
    
    # Ask for amount
    await message.reply_text(
        "💰 *Tambah Pemasukan*\n\n"
        "💵 Masukkan jumlah pemasukan:\n"
        "Contoh: 5000000, 5jt, 5 juta",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['transaction_type'] = 'income'
    return WAITING_FOR_AMOUNT

async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /expense command - add expense transaction"""
    user_id = update.effective_user.id
    
    # Determine message object (could be from command or callback)
    message = update.message if update.message else update.callback_query.message
    
    # Check if amount is provided in command
    if context.args:
        amount_text = ' '.join(context.args)
        amount = parse_amount(amount_text)
        
        if amount:
            # Store in context for next step
            context.user_data['transaction_type'] = 'expense'
            context.user_data['amount'] = amount
            
            await message.reply_text(
                f"💸 Pengeluaran: {format_currency(amount)}\n\n"
                "📝 Masukkan deskripsi pengeluaran:"
            )
            return WAITING_FOR_DESCRIPTION
    
    # Ask for amount
    await message.reply_text(
        "💸 *Tambah Pengeluaran*\n\n"
        "💵 Masukkan jumlah pengeluaran:\n"
        "Contoh: 150000, 150rb, 150 ribu",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['transaction_type'] = 'expense'
    return WAITING_FOR_AMOUNT

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - show financial reports"""
    user_id = update.effective_user.id
    
    # Determine message object (could be from command or callback)
    message = update.message if update.message else update.callback_query.message
    
    # Default to monthly report
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
            reply_markup=get_report_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await message.reply_text(
            "❌ Gagal membuat laporan. Silakan coba lagi."
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
            "• `/search hari ini` - Cari transaksi hari ini\n"
            "• `/search groceries` - Cari deskripsi groceries",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    search_query = ' '.join(context.args)
    
    try:
        results = await sheets_service.search_transactions(user_id, search_query)
        
        if not results:
            await message.reply_text(
                f"🔍 Tidak ditemukan transaksi untuk: *{search_query}*",
                parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error searching transactions: {e}")
        await message.reply_text(
            "❌ Gagal mencari transaksi. Silakan coba lagi."
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
            parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in AI command: {e}")
        await message.reply_text(
            "❌ AI sedang tidak tersedia. Silakan coba lagi nanti."
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

💡 Ketik /report untuk laporan lengkap
"""
        
        await message.reply_text(
            balance_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        await message.reply_text(
            "❌ Gagal mengambil saldo. Silakan coba lagi."
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
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error showing categories: {e}")
        await message.reply_text(
            "❌ Gagal menampilkan kategori. Silakan coba lagi."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Try to parse as transaction
    transaction_data = parse_transaction_text(message_text)
    
    if transaction_data:
        try:
            # Auto-detect category
            category = await sheets_service.detect_category(
                transaction_data['description'], 
                transaction_data['type']
            )
            
            # Add transaction
            success = await sheets_service.add_transaction(
                user_id=user_id,
                amount=transaction_data['amount'],
                description=transaction_data['description'],
                category=category,
                transaction_type=transaction_data['type']
            )
            
            if success:
                type_icon = "💰" if transaction_data['type'] == 'income' else "💸"
                await update.message.reply_text(
                    f"✅ Transaksi berhasil dicatat!\n\n"
                    f"{type_icon} *{transaction_data['type'].title()}:* {format_currency(transaction_data['amount'])}\n"
                    f"📝 *Deskripsi:* {transaction_data['description']}\n"
                    f"🏷️ *Kategori:* {category}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("❌ Gagal menyimpan transaksi. Silakan coba lagi.")
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            await update.message.reply_text("❌ Gagal memproses transaksi. Silakan coba lagi.")
    else:
        # If not a transaction, maybe it's a question for AI
        if len(message_text) > 10 and any(word in message_text.lower() for word in 
                                         ['analisis', 'tips', 'saran', 'bagaimana', 'kapan', 'berapa']):
            await update.message.reply_text(
                f"🤖 Untuk pertanyaan AI, gunakan: `/ai {message_text}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "❓ Saya tidak mengerti pesan Anda.\n\n"
                "💡 Contoh yang bisa saya pahami:\n"
                "• Beli makan 25000\n"
                "• Gaji bulan ini 5 juta\n"
                "• Atau gunakan /help untuk bantuan"
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
        elif data.startswith("category_"):
            # Handle category selection
            category = data.replace("category_", "")
            context.user_data['selected_category'] = category
            await process_transaction_with_category(update, context)
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

async def process_transaction_with_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process transaction after category selection"""
    user_data = context.user_data
    user_id = update.effective_user.id
    
    try:
        success = await sheets_service.add_transaction(
            user_id=user_id,
            amount=user_data.get('amount'),
            description=user_data.get('description'),
            category=user_data.get('selected_category'),
            transaction_type=user_data.get('transaction_type')
        )
        
        if success:
            type_icon = "💰" if user_data['transaction_type'] == 'income' else "💸"
            await update.callback_query.edit_message_text(
                f"✅ Transaksi berhasil dicatat!\n\n"
                f"{type_icon} *{user_data['transaction_type'].title()}:* {format_currency(user_data['amount'])}\n"
                f"📝 *Deskripsi:* {user_data['description']}\n"
                f"🏷️ *Kategori:* {user_data['selected_category']}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.callback_query.edit_message_text("❌ Gagal menyimpan transaksi.")
            
        # Clear user data
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"Error processing transaction with category: {e}")
        await update.callback_query.edit_message_text("❌ Terjadi kesalahan.")