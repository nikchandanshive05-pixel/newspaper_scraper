"""
Telegram bot for sending HTML notes and summaries.
"""

from telegram import Bot
from telegram.constants import ParseMode
import asyncio
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramSender:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID

    async def send_file(self, file_path: str, caption: str = None, filename: str = None) -> bool:
        """
        Send any file (HTML, PDF, etc.) to Telegram.
        """
        try:
            if not caption:
                caption = (
                    f"📰 <b>Daily Exam Notes</b>\n"
                    f"📅 {datetime.now().strftime('%B %d, %Y')}\n"
                    f"📚 UPSC | MPSC | SSC | Banking | RBI\n\n"
                    f"🤖 <i>Powered by Gemini 1.5 Pro</i>"
                )

            actual_filename = filename or file_path.split('/')[-1]

            with open(file_path, 'rb') as f:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=f,
                    filename=actual_filename,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )

            print("✅ File sent to Telegram successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to send file: {e}")
            return False

    def send_file_sync(self, file_path: str, caption: str = None, filename: str = None) -> bool:
        return asyncio.run(self.send_file(file_path, caption, filename))

    # Backward compatibility
    def send_pdf_sync(self, pdf_path: str, caption: str = None) -> bool:
        return self.send_file_sync(pdf_path, caption, filename="daily_exam_digest.pdf")
