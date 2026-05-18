import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT = """
أنت خبير في التحليل الفني للعملات الرقمية.
حلل هذا الشارت واعطني:
📊 الاتجاه العام
🔷 النماذج الفنية
🎯 سعر الدخول
✅ TP1 و TP2
🛑 وقف الخسارة SL
⚠️ هذا تحليل تعليمي فقط
"""

async def start(update, ctx):
    await update.message.reply_text("👋 أرسل صورة الشارت وسأحللها فوراً!")

async def analyze_chart(update, ctx):
    await update.message.reply_text("⏳ جاري التحليل...")
    try:
        photo = update.message.photo[-1]
        file = await ctx.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        import PIL.Image, io
        image = PIL.Image.open(io.BytesIO(img_bytes))
        response = model.generate_content([PROMPT, image])
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    app.run_polling()

if __name__ == "__main__":
    main()
