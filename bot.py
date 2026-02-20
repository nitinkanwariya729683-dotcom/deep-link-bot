import logging
import threading
import os
from flask import Flask

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

# ==================== YOUR BOT TOKEN ====================
TOKEN = "8281770546:AAEsYcyUgMoQ9SJKc5uu-JS9hKgcc2BtoT4"
DELETE_TIME = 1800  # 30 minutes
PRIVATE_CHANNEL_ID = -1003708551873  # Your private channel ID

# ====== ONLY ERROR LOGGING (No Spam in CMD) ======
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.ERROR
)

logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("apscheduler").setLevel(logging.CRITICAL)
logging.getLogger("telegram").setLevel(logging.CRITICAL)

# ================= START HANDLER =================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Invalid or expired link.")
        return

    channel_message_id = context.args[0]
    chat_id = update.effective_chat.id

    try:
        sent_msg = await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=PRIVATE_CHANNEL_ID,
            message_id=int(channel_message_id)
        )

        await context.bot.send_message(
            chat_id,
            "⚠️ Ye file 30 minute baad delete kar di jayegi 🫶"
        )

        context.job_queue.run_once(
            delete_message,
            DELETE_TIME,
            data={
                "chat_id": chat_id,
                "message_id": sent_msg.message_id
            }
        )

    except BadRequest:
        await update.message.reply_text("❌ This file is no longer available.")

# ================= DELETE FUNCTION =================
async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]

    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass

# ================= CHANNEL POST HANDLER =================
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg:
        return

    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={msg.message_id}"

    await msg.reply_text(
        f"✅ Media Saved Successfully!\n\n🔗 Deep Link:\n{deep_link}"
    )

# ================= FLASK PORT FIX FOR RENDER =================
def start_web_server():
    web_app = Flask(__name__)

    @web_app.route("/")
    def home():
        return "Bot is running!"

    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))

    # Start Flask in separate thread (Render ke liye)
    threading.Thread(target=start_web_server).start()

    print("Bot Started Successfully ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
