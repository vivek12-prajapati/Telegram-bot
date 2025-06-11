from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

# Store user preferences
user_langs = {}
speak_only_users = set()

# Language options for inline buttons
language_buttons = [
    [InlineKeyboardButton("English 🇬🇧", callback_data='en'), InlineKeyboardButton("Hindi 🇮🇳", callback_data='hi')],
    [InlineKeyboardButton("Spanish 🇪🇸", callback_data='es'), InlineKeyboardButton("French 🇫🇷", callback_data='fr')],
    [InlineKeyboardButton("Chinese 🇨🇳", callback_data='zh-CN'), InlineKeyboardButton("German 🇩🇪", callback_data='de')]
]

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *Welcome to LangBot!*\n\n"
        "I can help you translate and speak any text.\n\n"
        "📌 Use the buttons below to choose your target language.\n"
        "🗣️ Send me any message and I'll translate and speak it.\n\n"
        "`/speakonly` – Toggle audio-only mode"
    )
    reply_markup = InlineKeyboardMarkup(language_buttons)
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

# Handle language selection from inline buttons
async def language_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang_code = query.data
    user_id = query.from_user.id
    user_langs[user_id] = lang_code

    await query.edit_message_text(
        f"✅ Target language set to `{lang_code}`.\n\nNow send me a message to translate!",
        parse_mode='Markdown'
    )

# /speakonly toggle
async def toggle_speakonly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in speak_only_users:
        speak_only_users.remove(user_id)
        await update.message.reply_text("📝 Speak-only mode disabled.")
    else:
        speak_only_users.add(user_id)
        await update.message.reply_text("🔊 Speak-only mode enabled. You will receive only audio replies.")

# Main translator + TTS logic
async def translate_and_speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    target_lang = user_langs.get(user_id, 'en')  # Default to English

    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)

        # Save to history
        with open("translations.txt", "a", encoding='utf-8') as f:
            f.write(f"User: {user_id}\nFrom: {text}\nTo ({target_lang}): {translated}\n---\n")

        if user_id not in speak_only_users:
            await update.message.reply_text(f"📘 Translation:\n{translated}")

        tts = gTTS(translated, lang=target_lang)
        filename = f"voice_{user_id}.mp3"
        tts.save(filename)
        await update.message.reply_voice(voice=open(filename, 'rb'))
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# --------------------- 
# Setup your bot
# ---------------------
TOKEN = "8104780340:AAFq8uGLpTNYU2v0Dk2GWJMLmUYJrMJ_d5k"

app = Application.builder().token(TOKEN).build()

# Register handlers
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("speakonly", toggle_speakonly))
app.add_handler(CallbackQueryHandler(language_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_and_speak))

print("✅ Bot is running...")
app.run_polling()
