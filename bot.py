import os
import shutil
import logging
import asyncio
import time
from collections import defaultdict

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN
from downloader import search_youtube, download_audio_file

logging.basicConfig(level=logging.INFO)

TMP_BASE = "tmp"
INACTIVITY_TIMEOUT = 600  # 10 minutes

user_queues = defaultdict(asyncio.Queue)
user_tasks = {}
last_active = {}

def get_user_tmp_path(user_id):
    return os.path.join(TMP_BASE, str(user_id))

def ensure_tmp_path(user_id):
    path = get_user_tmp_path(user_id)
    os.makedirs(path, exist_ok=True)
    return path

def clear_tmp_for_user(user_id):
    user_path = get_user_tmp_path(user_id)
    if os.path.exists(user_path):
        shutil.rmtree(user_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a track name and I'll find and send it to you 🎶")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    # Сохраняем активность
    last_active[user_id] = time.time()

    # Создаём очередь пользователя и добавляем туда запрос
    queue = user_queues[user_id]
    await queue.put((message_text, update))

    # Если воркер уже работает — не запускаем второй
    if user_id in user_tasks:
        await update.message.reply_text("⏳ Please wait for the current track to finish.")
        return

    # Запускаем обработчик очереди
    user_tasks[user_id] = asyncio.create_task(process_user_queue(user_id, context))

async def process_user_queue(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    queue = user_queues[user_id]

    while not queue.empty():
        query, update = await queue.get()
        is_first = queue.qsize() == 0

        if not is_first:
            await update.message.reply_text("▶️ Now searching for the next track...")
        try:
            await update.message.reply_text("🔎 Searching and downloading the track...")
            results = search_youtube(query)
            if not results:
                await update.message.reply_text("No results found 😢")
                continue

            url = results[0]['url']
            title = results[0]['title']
            user_tmp = ensure_tmp_path(user_id)
            file_path, actual_title = download_audio_file(url, user_tmp)

            await update.message.reply_audio(audio=open(file_path, 'rb'), title=actual_title or title)
        except Exception as e:
            logging.error(f"Error for user {user_id}: {e}")

    # Очистка после завершения очереди
    user_tasks.pop(user_id, None)

async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for user_id, last_time in list(last_active.items()):
            if now - last_time > INACTIVITY_TIMEOUT:
                clear_tmp_for_user(user_id)
                logging.info(f"Cleared tmp for user {user_id} due to inactivity.")
                del last_active[user_id]
                user_queues.pop(user_id, None)

if __name__ == "__main__":
    os.makedirs(TMP_BASE, exist_ok=True)

    async def on_startup(app):
        asyncio.create_task(cleanup_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    app.run_polling()