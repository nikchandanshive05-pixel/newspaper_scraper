"""
Telegram bot for sending PDF.
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
        try:
            if not caption:
                from datetime import datetime
                caption = (
                    f"📰 <b>Daily Exam News Digest</b>\n"
                    f"📅 {datetime.now().strftime('%B %d, %Y')}\n"
                    f"📚 UPSC | MPSC | SSC | Banking | RBI"
                )

            with open(pdf_path, 'rb') as pdf_file:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=pdf_file,
                    filename="daily_exam_digest.pdf",
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )

            print("✅ PDF sent to Telegram successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to send PDF: {e}")
            return False

    def send_pdf_sync(self, pdf_path: str, caption: str = None) -> bool:
        return asyncio.run(self.send_pdf(pdf_path, caption))
