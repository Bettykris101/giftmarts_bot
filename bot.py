import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inventory data
INVENTORY = {
    "gaming": {
        "name": "🎮 Gaming Cards",
        "items": [
            "PlayStation Store ($10) - In Stock",
            "Xbox Gift Card ($25) - In Stock",
            "Steam Wallet ($50) - In Stock",
            "Nintendo eShop ($20) - Low Stock"
        ]
    },
    "entertainment": {
        "name": "🎬 Entertainment & Streaming",
        "items": [
            "Netflix Gift Card - In Stock",
            "Spotify Premium - In Stock",
            "Disney+ Subscription - In Stock",
            "Hulu Gift Card - Out of Stock"
        ]
    },
    "retail": {
        "name": "🛍️ Retail & Shopping",
        "items": [
            "Amazon Gift Card - In Stock",
            "Walmart eGift Card - In Stock",
            "Target GiftCard - In Stock",
            "Best Buy Gift Card - Low Stock"
        ]
    }
}

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with main menu."""
    user = update.effective_user
    welcome_text = (
        f"Hi {user.first_name}!\n\n"
        "Welcome to the Giftmart Catalog!\n"
        "Use the menu buttons below to browse authentic, officially licensed "
        "digital gift cards for gaming, streaming, and retail shopping.\n\n"
        "Please choose a category to check live stock:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 Gaming Cards", callback_data="gaming")],
        [InlineKeyboardButton("🎬 Entertainment & Streaming", callback_data="entertainment")],
        [InlineKeyboardButton("🛍️ Retail & Shopping", callback_data="retail")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle category button clicks."""
    query = update.callback_query
    await query.answer()
    
    category_key = query.data
    category_info = INVENTORY.get(category_key)
    
    if category_info:
        # Create a formatted stock list
        stock_items = "\n".join([f"• {item}" for item in category_info["items"]])
        message = (
            f"📦 *{category_info['name']} - Live Stock:*\n\n"
            f"{stock_items}\n\n"
            "💡 *To purchase:* Contact @support_username (Coming Soon)"
        )
        await query.edit_message_text(message, parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ Category not found. Use /start to return to main menu.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    await update.message.reply_text(
        "🤖 *Giftmart Bot Help*\n\n"
        "• /start - Open main catalog\n"
        "• /help - Show this help message\n"
        "• /stock - Check all available categories\n\n"
        "For support, please contact our team."
    )

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all categories with stock status."""
    message = "📊 *All Categories:*\n\n"
    for key, category in INVENTORY.items():
        available = sum(1 for item in category["items"] if "In Stock" in item)
        total = len(category["items"])
        message += f"• {category['name']}: {available}/{total} items in stock\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

def main() -> None:
    """Start the bot."""
    # Get token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    logger.info("🚀 Starting Giftmart bot...")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start polling
    logger.info("✅ Bot is running and listening for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
