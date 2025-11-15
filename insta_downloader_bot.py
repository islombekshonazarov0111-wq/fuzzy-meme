import os
import asyncio
from yt_dlp import YoutubeDL
from telegram import (
    Update,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# === Sozlamalar ===
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = "@attackboy_pubgm"
CHANNEL_URL = "https://t.me/attackboy_pubgm"

TMP_DIR = "tmp_media"
os.makedirs(TMP_DIR, exist_ok=True)


# === OBUNA TEKSHIRISH ===
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ("left", "kicked")
    except:
        return False


def subscription_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Obuna bo‘lish", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Obuna bo‘ldim — Tekshirish", callback_data="check_subscription")]
    ])


# === Start komandasi ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n"
        "Menga Instagram, YouTube, TikTok yoki boshqa link yuboring — men uni yuklab beraman.\n\n"
        "🎵 Faqat musiqa uchun: /music <link>\n\n"
        f"📌 Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling!"
    )


# === Media yuklab olish ===
def ytdl_download(url, opts):
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        if "postprocessors" in opts:
            file = os.path.splitext(file)[0] + ".mp3"
        return file, info


video_opts = {
    "format": "best",
    "outtmpl": TMP_DIR + "/%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True
}

audio_opts = {
    "format": "bestaudio/best",
    "outtmpl": TMP_DIR + "/%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
    ]
}


# === Yuklab berish funksiyasi ===
async def process_media(msg, context, url, opts, is_audio=False):
    loading = await msg.reply_text("⏳ Yuklanmoqda...")

    try:
        loop = asyncio.get_running_loop()
        filename, info = await loop.run_in_executor(None, lambda: ytdl_download(url, opts))

        title = info.get("title", "Media")
        caption = f"📥 Yuklandi: {title}"

        ext = os.path.splitext(filename)[1]

        with open(filename, "rb") as f:
            if is_audio or ext in [".mp3", ".m4a", ".aac", ".ogg"]:
                await msg.reply_audio(InputFile(f, filename=filename), caption=caption)

            elif ext in [".mp4", ".mov", ".mkv", ".avi"]:
                await msg.reply_video(InputFile(f), caption=caption)

            elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
                await msg.reply_photo(InputFile(f), caption=caption)

            else:
                await msg.reply_document(InputFile(f), caption=caption)

        await loading.delete()

    except Exception as e:
        await loading.edit_text(f"❌ Xatolik: {e}")

    finally:
        for f in os.listdir(TMP_DIR):
            try:
                os.remove(TMP_DIR + "/" + f)
            except:
                pass


# === Oddiy link kelganda ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text or ""

    if not text.startswith("http"):
        await msg.reply_text("❌ Iltimos, to‘liq link yuboring.")
        return

    if not await is_subscribed(msg.from_user.id, context):
        await msg.reply_text(
            f"📢 Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling!",
            reply_markup=subscription_keyboard()
        )
        return

    await process_media(msg, context, text, video_opts)


# === /music komandasi ===
async def handle_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    args = context.args
    link = args[0] if args else msg.text.replace("/music", "").strip()

    if not link.startswith("http"):
        await msg.reply_text("🎵 Iltimos musiqa link yuboring.")
        return

    if not await is_subscribed(msg.from_user.id, context):
        await msg.reply_text(
            f"🎧 Musiqa olish uchun avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )
        return

    await process_media(msg, context, link, audio_opts, is_audio=True)


# === Obunani tekshirish tugmasi ===
async def callback_check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if await is_subscribed(q.from_user.id, context):
        await q.edit_message_text("✅ Obuna tasdiqlandi! Endi link yuboring.")
    else:
        await q.edit_message_text(
            "❌ Hali obuna emassiz!",
            reply_markup=subscription_keyboard()
        )


# === Botni ishga tushirish ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", handle_music))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_check_subscription, pattern="check_subscription"))

    print("✅ Bot ishga tushdi...")
    app.run_polling()


if _name_ == "_main_":

    main()
