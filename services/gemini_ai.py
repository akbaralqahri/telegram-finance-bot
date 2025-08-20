"""
Gemini AI service for Finance Bot
Handles AI-powered financial analysis and advice
"""

import logging
import json
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
            if not Config.GEMINI_API_KEY:
                logger.error("Gemini API key not found")
                return False
            
            # Configure Gemini
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            
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
            
            return response
            
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
        return f"""
{Config.AI_SYSTEM_PROMPT}

KONTEKS KEUANGAN USER:
{context}

PERTANYAAN USER: {user_question}

Berikan jawaban yang:
1. Spesifik berdasarkan data keuangan user
2. Praktis dan bisa diterapkan
3. Menggunakan angka konkret jika relevan
4. Ramah dan mudah dipahami
5. Dalam bahasa Indonesia

Jika pertanyaan tidak berhubungan dengan keuangan, arahkan kembali ke topik keuangan dengan sopan.
"""
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini AI"""
        try:
            if not self.model:
                return "AI service tidak tersedia."
            
            # Generate content
            response = self.model.generate_content(prompt)
            
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
            else:
                return "❌ Terjadi kesalahan pada AI service. Silakan coba lagi nanti."