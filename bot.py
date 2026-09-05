import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inventory (Your Static "Database") ---
# In a real scenario, you could read this from a file or a spreadsheet.
# For now, it's a Python dictionary. You can expand this.
INVENTORY = {
    "gaming": {"name": "🎮 Gaming Cards", "items": ["PlayStation Store ($10)", "Xbox Gift Card ($25)", "Steam Wallet ($50)"]},
    "entertainment": {"name": "🎬 Entertainment & Streaming", "items": ["Netflix Gift Card", "Spotify Premium", "Disney+ Subscription"]},
    "retail": {"name": "🛍️ Retail & Shopping", "items": ["Amazon Gift Card", "Walmart eGift Card", "Target GiftCard"]},
}

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and show the main menu."""
    user = update.effective_user
    welcome_text = (
        f"Hi {user.first_name}!\n\n"
        "Welcome to the Giftmart Catalog!\n"
        "Use the menu buttons below to browse authentic, officially licensed digital gift cards "
        "for gaming, streaming, and retail shopping.\n\n"
        "Please choose a category to check live stock:"
    )
    keyboard = [
        [InlineKeyboardButton("🎮 Gaming cards", callback_data="gaming")],
        [InlineKeyboardButton("🎬 Entertainment and streaming", callback_data="entertainment")],
        [InlineKeyboardButton("🛍️ Retail and shopping", callback_data="retail")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the button presses and show stock."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    category_key = query.data
    category_info = INVENTORY.get(category_key)

    if category_info:
        stock_list = "\n".join([f"• {item}" for item in category_info["items"]])
        message = (
            f"📦 *{category_info['name']} - Live Stock:*\n"
            f"{stock_list}\n\n"
            "_To purchase, please contact support (feature coming soon)._"
        )
        await query.edit_message_text(message, parse_mode="Markdown")
    else:
        await query.edit_message_text("Category not found. Please use /start to go back to the main menu.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    await update.message.reply_text("Use /start to see the main catalog.")

# --- Main Function ---

def main() -> None:
    """Start the bot."""
    # Get the bot token from environment variables (essential for Railway)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN set. Please set this environment variable.")
        return

    # Create the Application
    application = Application.builder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
