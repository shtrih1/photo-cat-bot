import logging
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = "YOUR_BOT_TOKEN"
BASE_URL = "https://cataas.com/cat"

# user_id: hour
user_schedule = {}
scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

# Получить случайную фотку кота с сайта Cataas.com
def get_cat_url():
    return f"{BASE_URL}?{random.randint(1, 100000)}"

# Кнопки
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌈 Хочу котика сейчас", callback_data="cat_now")],
        [InlineKeyboardButton("🌟 Изменить время", callback_data="change_time")],
    ])

def get_time_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{hour}:00", callback_data=f"set_time_{hour}")]
        for hour in range(8, 23)
    ])

async def send_cat(chat_id, context):
    url = get_cat_url()
    await context.bot.send_photo(chat_id=chat_id, photo=url, caption="Вот тебе котик 😺", reply_markup=get_main_keyboard())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я буду присылать тебе котиков! 😺", reply_markup=get_main_keyboard())

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cat_now":
        await send_cat(query.message.chat_id, context)

    elif query.data == "change_time":
        await query.message.reply_text("Выбери время, в которое тебе будет приходить котик:", reply_markup=get_time_keyboard())

    elif query.data.startswith("set_time_"):
        hour = int(query.data.split("_")[-1])
        user_id = query.from_user.id
        user_schedule[user_id] = hour

        # Удаляем старую задачу, если была
        scheduler.remove_job(str(user_id)) if scheduler.get_job(str(user_id)) else None
        
        scheduler.add_job(send_cat, CronTrigger(hour=hour, minute=0), args=[user_id, context], id=str(user_id))

        await query.message.reply_text(f"✅ Отлично! Я пришлю тебе котика в {hour}:00 каждый день.", reply_markup=get_main_keyboard())

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Нажми кнопку снизу. ", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler.start()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    print("Bot is running...")
    app.run_polling()
