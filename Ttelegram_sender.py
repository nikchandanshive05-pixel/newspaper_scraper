"""
Telegram bot module for sending PDF files.
"""

from telegram import Bot
from telegram.constants import ParseMode
import asyncio
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramSender:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID
        
    async def send_pdf(self, pdf_path: str, caption: str = None) -> bool:
        """
        Send PDF file to Telegram chat.
        """
        try:
            if not caption:
                from datetime import datetime
                caption = f"📰 Daily Newspaper Digest\n📅 {datetime.now().strftime('%B %d, %Y')}"
            
            with open(pdf_path, 'rb') as pdf_file:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=pdf_file,
                    filename="daily_newspaper.pdf",
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
            print("✅ PDF sent successfully to Telegram!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send PDF: {e}")
            return False
    
    def send_pdf_sync(self, pdf_path: str, caption: str = None) -> bool:
        """Synchronous wrapper for sending PDF."""
        return asyncio.run(self.send_pdf(pdf_path, caption))
      
