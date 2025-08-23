"""
Bot package initialization - FIXED VERSION
"""

# FIXED: Import only the functions that actually exist in handlers.py
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
    handle_callback,
    setup_bot_menu,
    get_conversation_handler,
    # Removed any non-existent imports
)

from .keyboards import (
    get_main_keyboard,
    get_persistent_keyboard,
    get_quick_action_keyboard,
    get_minimal_keyboard,
    get_date_keyboard,
    get_confirmation_keyboard,
    get_report_keyboard,
    get_bot_commands,
)

__all__ = [
    # Handler functions
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
    'setup_bot_menu',
    'get_conversation_handler',
    
    # Keyboard functions
    'get_main_keyboard',
    'get_persistent_keyboard',
    'get_quick_action_keyboard',
    'get_minimal_keyboard',
    'get_date_keyboard',
    'get_confirmation_keyboard', 
    'get_report_keyboard',
    'get_bot_commands',
]