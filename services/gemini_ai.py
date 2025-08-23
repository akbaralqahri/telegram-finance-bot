"""
Gemini AI service for Finance Bot - CLEAN VERSION (No Syntax Errors)
Handles AI-powered financial analysis and advice
"""

import logging
import json
import re
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime

from config import Config
from utils.helpers import format_currency

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service for AI-powered financial analysis using Gemini"""
    
    def __init__(self):
        self.model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Gemini AI service"""
        try:
            if not hasattr(Config, 'GEMINI_API_KEY') or not Config.GEMINI_API_KEY:
                logger.error("Gemini API key not found")
                return False
            
            # Configure Gemini
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            self.is_initialized = True
            logger.info("Gemini AI service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI service: {e}")
            return False
    
    async def get_financial_advice(self, user_question: str, financial_data: Dict) -> str:
        """Get AI-powered financial advice based on user data"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not self.model:
                return "AI service sedang tidak tersedia. Silakan coba lagi nanti."
            
            # Prepare context with user's financial data
            context = self._prepare_financial_context(financial_data)
            
            # Create comprehensive prompt
            prompt = self._build_advice_prompt(user_question, context)
            
            # Generate response
            response = await self._generate_response(prompt)
            
            # FIXED: Clean response for Telegram compatibility
            cleaned_response = self._clean_response_for_telegram(response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error getting financial advice: {e}")
            return "Maaf, terjadi kesalahan saat memproses permintaan AI. Silakan coba lagi."
    
    def _prepare_financial_context(self, financial_data: Dict) -> str:
        """Prepare financial data context for AI"""
        try:
            context = "DATA KEUANGAN USER:\n"
            
            # Current balance
            current_balance = financial_data.get('current_balance', 0)
            context += f"💰 Saldo Saat Ini: {format_currency(current_balance)}\n"
            
            # This month summary
            this_month = financial_data.get('this_month', {})
            context += f"\n📊 BULAN INI:\n"
            context += f"• Pemasukan: {format_currency(this_month.get('income', 0))}\n"
            context += f"• Pengeluaran: {format_currency(this_month.get('expense', 0))}\n"
            context += f"• Net: {format_currency(this_month.get('net', 0))}\n"
            
            # Last month comparison
            last_month = financial_data.get('last_month', {})
            if last_month:
                context += f"\n📈 BULAN LALU (PERBANDINGAN):\n"
                context += f"• Pemasukan: {format_currency(last_month.get('income', 0))}\n"
                context += f"• Pengeluaran: {format_currency(last_month.get('expense', 0))}\n"
                context += f"• Net: {format_currency(last_month.get('net', 0))}\n"
                
                # Calculate trends
                income_trend = ((this_month.get('income', 0) - last_month.get('income', 0)) / max(last_month.get('income', 1), 1)) * 100
                expense_trend = ((this_month.get('expense', 0) - last_month.get('expense', 0)) / max(last_month.get('expense', 1), 1)) * 100
                context += f"• Tren Pemasukan: {income_trend:+.1f}%\n"
                context += f"• Tren Pengeluaran: {expense_trend:+.1f}%\n"
            
            # Top spending categories
            top_categories = financial_data.get('top_categories', [])
            if top_categories:
                context += f"\n🏷️ TOP KATEGORI PENGELUARAN BULAN INI:\n"
                for i, (category, amount) in enumerate(top_categories[:5], 1):
                    percentage = (amount / max(this_month.get('expense', 1), 1)) * 100
                    context += f"{i}. {category}: {format_currency(amount)} ({percentage:.1f}%)\n"
            
            # Recent transactions
            recent_transactions = financial_data.get('recent_transactions', [])
            if recent_transactions:
                context += f"\n📝 TRANSAKSI TERBARU:\n"
                for trans in recent_transactions[-3:]:  # Last 3 transactions
                    amount_str = format_currency(abs(trans.get('amount', 0)))
                    type_indicator = "+" if trans.get('amount', 0) > 0 else "-"
                    context += f"• {trans.get('description', '')}: {type_indicator}{amount_str}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing financial context: {e}")
            return "Data keuangan tidak tersedia untuk analisis."
    
    def _build_advice_prompt(self, user_question: str, context: str) -> str:
        """Build comprehensive prompt for financial advice"""
        system_prompt = getattr(Config, 'AI_SYSTEM_PROMPT', 
            "Anda adalah asisten keuangan yang membantu pengguna mengelola keuangan mereka dengan memberikan saran yang praktis dan mudah dipahami.")
        
        return f"""
{system_prompt}

KONTEKS KEUANGAN USER:
{context}

PERTANYAAN USER: {user_question}

INSTRUKSI RESPONSE:
1. Berikan jawaban dalam bahasa Indonesia yang sederhana dan mudah dipahami
2. Gunakan data konkret dari konteks keuangan user
3. Berikan saran yang praktis dan actionable
4. Hindari penggunaan karakter khusus yang berlebihan
5. Format response dengan struktur yang jelas
6. Jangan gunakan bold atau italic berlebihan
7. Maksimal 500 kata

Jika pertanyaan tidak berhubungan dengan keuangan, arahkan kembali ke topik keuangan dengan sopan.
"""
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini AI"""
        try:
            if not self.model:
                return "AI service tidak tersedia."
            
            # Generate content with safety settings
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1000,
                }
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "Maaf, AI tidak dapat memberikan respons saat ini."
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            
            # Handle common errors
            if "quota" in str(e).lower():
                return "🚫 Quota AI sudah habis untuk hari ini. Silakan coba lagi besok."
            elif "safety" in str(e).lower():
                return "🛡️ Pertanyaan tidak dapat diproses karena alasan keamanan. Silakan ajukan pertanyaan yang berbeda."
            elif "blocked" in str(e).lower():
                return "🚫 Respons diblokir karena alasan keamanan. Silakan ajukan pertanyaan yang berbeda."
            else:
                return "❌ Terjadi kesalahan pada AI service. Silakan coba lagi nanti."
    
    def _clean_response_for_telegram(self, response: str) -> str:
        """FIXED: Clean AI response for Telegram compatibility"""
        try:
            if not response:
                return "Tidak ada respons dari AI."
            
            # Remove or fix problematic characters
            cleaned = response
            
            # Fix common markdown issues
            # Remove excessive bold/italic markers
            cleaned = re.sub(r'\*{3,}', '**', cleaned)  # Reduce multiple * to **
            cleaned = re.sub(r'_{3,}', '__', cleaned)   # Reduce multiple _ to __
            
            # Fix unmatched markdown
            # Count asterisks and fix unmatched ones
            asterisk_count = cleaned.count('*')
            if asterisk_count % 2 != 0:
                # Add closing asterisk if unmatched
                cleaned = cleaned + '*'
            
            # Fix unmatched underscores
            underscore_count = cleaned.count('_')
            if underscore_count % 2 != 0:
                # Add closing underscore if unmatched
                cleaned = cleaned + '_'
            
            # Remove problematic characters that can cause parsing issues
            # Remove zero-width characters and other invisible characters
            cleaned = re.sub(r'[\u200b-\u200f\u2060-\u206f]', '', cleaned)
            
            # Fix bullet points and special characters
            cleaned = re.sub(r'[•◦▪▫]', '•', cleaned)  # Standardize bullet points
            cleaned = re.sub(r'["""]', '"', cleaned)   # Standardize quotes
            cleaned = re.sub(r"['']", "'", cleaned)   # FIXED: Standardize apostrophes (no smart quotes)
            
            # Ensure proper line breaks
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max 2 consecutive line breaks
            
            # Remove leading/trailing whitespace
            cleaned = cleaned.strip()
            
            # Truncate if too long (Telegram has limits)
            if len(cleaned) > 4000:
                cleaned = cleaned[:3900] + "...\n\n✂️ Respons dipotong karena terlalu panjang."
            
            # FIXED: Escape problematic markdown sequences
            # Handle common markdown parsing issues
            problematic_patterns = [
                (r'\*([^*\n]{0,5})\*([^*\n]{0,5})\*', r'*\1*\2'),  # Fix triple asterisks
                (r'_([^_\n]{0,5})_([^_\n]{0,5})_', r'_\1_\2'),     # Fix triple underscores
                (r'\[([^\]]*)\]\(([^)]*)\)', r'\1 (\2)'),          # Fix broken links
            ]
            
            for pattern, replacement in problematic_patterns:
                cleaned = re.sub(pattern, replacement, cleaned)
            
            # Final validation - if still problematic, fall back to plain text
            if self._has_markdown_issues(cleaned):
                logger.warning("Response has markdown issues, converting to plain text")
                cleaned = self._convert_to_plain_text(cleaned)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning response for Telegram: {e}")
            # Fallback to plain text
            return self._convert_to_plain_text(response)
    
    def _has_markdown_issues(self, text: str) -> bool:
        """Check if text has markdown parsing issues"""
        try:
            # Check for unmatched markdown
            asterisk_count = text.count('*')
            underscore_count = text.count('_')
            
            # Basic checks for problematic patterns
            if asterisk_count % 2 != 0 or underscore_count % 2 != 0:
                return True
            
            # Check for problematic sequences
            problematic_sequences = [
                r'\*\*\*+',  # Too many asterisks
                r'___+',     # Too many underscores
                r'\[[^\]]*$', # Unclosed brackets
                r'[^\x00-\x7F]{10,}',  # Too many non-ASCII characters
            ]
            
            for pattern in problematic_sequences:
                if re.search(pattern, text):
                    return True
            
            return False
            
        except Exception:
            return True  # If we can't check, assume there are issues
    
    def _convert_to_plain_text(self, text: str) -> str:
        """Convert markdown text to plain text"""
        try:
            if not text:
                return "Tidak ada respons dari AI."
            
            # Remove all markdown formatting
            plain = text
            plain = re.sub(r'\*\*([^*]+)\*\*', r'\1', plain)  # Bold
            plain = re.sub(r'\*([^*]+)\*', r'\1', plain)      # Italic
            plain = re.sub(r'__([^_]+)__', r'\1', plain)      # Bold underscore
            plain = re.sub(r'_([^_]+)_', r'\1', plain)        # Italic underscore
            plain = re.sub(r'`([^`]+)`', r'\1', plain)        # Code
            plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)  # Links
            
            # Clean up extra whitespace
            plain = re.sub(r'\n{3,}', '\n\n', plain)
            plain = plain.strip()
            
            return plain
            
        except Exception as e:
            logger.error(f"Error converting to plain text: {e}")
            return "Maaf, terjadi kesalahan dalam memproses respons AI."