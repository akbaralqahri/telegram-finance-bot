"""
Bot package for Telegram Finance Bot
Contains handlers, keyboards, and bot-related functionality
"""

from .handlers import (
    start_command,
    help_command, 
    income_command,
    expense_command,
    report_command,
    search_command,
    ai_command,
    balance_command,
    categories_command,
    handle_message,
    handle_callback
)

from .keyboards import (
    get_main_keyboard,
    get_transaction_type_keyboard,
    get_category_keyboard,
    get_report_keyboard,
    get_confirmation_keyboard,
    get_amount_quick_keyboard,
    get_period_keyboard,
    get_search_type_keyboard,
    get_ai_suggestions_keyboard
)

__all__ = [
    # Handlers
    'start_command',
    'help_command',
    'income_command', 
    'expense_command',
    'report_command',
    'search_command',
    'ai_command',
    'balance_command',
    'categories_command',
    'handle_message',
    'handle_callback',
    
    # Keyboards
    'get_main_keyboard',
    'get_transaction_type_keyboard',
    'get_category_keyboard',
    'get_report_keyboard',
    'get_confirmation_keyboard',
    'get_amount_quick_keyboard',
    'get_period_keyboard',
    'get_search_type_keyboard',
    'get_ai_suggestions_keyboard'
]