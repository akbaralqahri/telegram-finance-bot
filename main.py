"""
Telegram Finance Bot - Main Application
Author: Finance Bot Developer
Created: 2024
"""

import logging
import asyncio
import signal
import sys
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Import local modules
from config import Config
from bot.handlers import (
    start_command, help_command, income_command, expense_command,
    report_command, search_command, ai_command, balance_command,
    categories_command, handle_message, handle_callback
)

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Configure logging with proper encoding
class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Replace problematic characters for Windows console
            if sys.platform == "win32":
                msg = msg.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARN]')
                msg = msg.replace('🚫', '[BLOCKED]').replace('🔧', '[SETUP]').replace('📊', '[DATA]')
                msg = msg.replace('💰', '[MONEY]').replace('🤖', '[AI]').replace('📱', '[BOT]')
            
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Setup logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler (supports UTF-8)
file_handler = logging.FileHandler('finance_bot.log', encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Console handler (safe for Windows)
console_handler = SafeStreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Set httpx and telegram.ext logging to WARNING to reduce noise
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class FinanceBot:
    def __init__(self):
        """Initialize the Finance Bot"""
        self.application = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize bot application and handlers"""
        try:
            # Validate configuration
            Config.validate_config()
            logger.info("Configuration validated successfully")
            
            # Create application
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            # Import conversation handler
            from bot.handlers import get_conversation_handler
            
            # Add conversation handler for step-by-step transaction input
            conv_handler = get_conversation_handler()
            self.application.add_handler(conv_handler)
            
            # Add command handlers (non-conversation)
            command_handlers = [
                CommandHandler("start", start_command),
                CommandHandler("help", help_command),
                CommandHandler("report", report_command),
                CommandHandler("search", search_command),
                CommandHandler("ai", ai_command),
                CommandHandler("balance", balance_command),
                CommandHandler("categories", categories_command),
            ]
            
            for handler in command_handlers:
                self.application.add_handler(handler)
            
            # Add message and callback handlers (with lower priority)
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=1)
            self.application.add_handler(CallbackQueryHandler(handle_callback), group=1)
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            logger.info("Bot handlers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors that occur during bot operation"""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Send error message to user if possible
        if update and update.effective_chat:
            try:
                await update.effective_chat.send_message(
                    "🚫 Maaf, terjadi kesalahan. Silakan coba lagi dalam beberapa saat."
                )
            except Exception:
                pass
    
    async def start(self):
        """Start the bot"""
        try:
            await self.initialize()
            
            logger.info("Starting Finance Bot...")
            await self.application.initialize()
            await self.application.start()
            
            self.is_running = True
            logger.info("[OK] Finance Bot started successfully!")
            logger.info("Bot is now running. Press Ctrl+C to stop.")
            
            # Start polling
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.application and self.is_running:
            logger.info("Stopping Finance Bot...")
            self.is_running = False
            
            # Stop polling and application
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            logger.info("[OK] Finance Bot stopped successfully!")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Shutting down...")
    
    # Create a new event loop for cleanup if none exists
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Schedule shutdown
    if hasattr(signal_handler, 'bot_instance'):
        loop.create_task(signal_handler.bot_instance.stop())
    
    # Exit gracefully
    sys.exit(0)

async def main():
    """Main function to run the bot"""
    # Create bot instance
    bot = FinanceBot()
    
    # Store bot instance for signal handler
    signal_handler.bot_instance = bot
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the bot
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Ensure cleanup
        await bot.stop()

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Error: Python 3.8 or higher is required")
            sys.exit(1)
        
        # Create necessary directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Run the bot
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n[INFO] Finance Bot stopped by user")
    except Exception as e:
        print(f"[ERROR] Failed to start Finance Bot: {e}")
        sys.exit(1)