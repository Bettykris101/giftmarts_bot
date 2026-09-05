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

# Inventory data - You can update this anytime
INVENTORY = {
    "gaming": {
        "name": "🎮 Gaming Cards",
        "items": [
            "🎮 PlayStation Store ($10) - ✅ In Stock",
            "🎮 Xbox Gift Card ($25) - ✅ In Stock", 
            "🎮 Steam Wallet ($50) - ✅ In Stock",
            "🎮 Nintendo eShop ($20) - ⚠️ Low Stock",
            "🎮 Roblox Gift Card - ✅ In Stock"
        ]
    },
    "entertainment": {
        "name": "🎬 Entertainment & Streaming",
        "items": [
            "🎬 Netflix Gift Card - ✅ In Stock",
            "🎬 Spotify Premium - ✅ In Stock",
            "🎬 Disney+ Subscription - ✅ In Stock",
            "🎬 Hulu Gift Card - ❌ Out of Stock",
            "🎬 Apple Music - ✅ In Stock"
        ]
    },
    "retail": {
        "name": "🛍️ Retail & Shopping",
        "items": [
            "🛍️ Amazon Gift Card - ✅ In Stock",
            "🛍️ Walmart eGift Card - ✅ In Stock",
            "🛍️ Target GiftCard - ✅ In Stock",
            "🛍️ Best Buy Gift Card - ⚠️ Low Stock",
            "🛍️ eBay Gift Card - ✅ In Stock"
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with main menu buttons."""
    user = update.effective_user
    
    welcome_text = (
        f"👋 *Hi {user.first_name}!*\n\n"
        "🏪 *Welcome to the Giftmart Catalog!*\n"
        "Use the menu buttons below to browse authentic, officially licensed "
        "digital gift cards for gaming, streaming, and retail shopping.\n\n"
        "📦 *Please choose a category to check live stock:*"
    )
    
    # Create inline keyboard with buttons
    keyboard = [
        [InlineKeyboardButton("🎮 Gaming Cards", callback_data="gaming")],
        [InlineKeyboardButton("🎬 Entertainment & Streaming", callback_data="entertainment")],
        [InlineKeyboardButton("🛍️ Retail & Shopping", callback_data="retail")],
        [InlineKeyboardButton("📊 View All Categories", callback_data="all_categories")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button clicks."""
    query = update.callback_query
    
    # Always answer the callback query first
    await query.answer()
    
    logger.info(f"Button clicked: {query.data}")
    
    if query.data == "all_categories":
        # Show all categories with stock summary
        message = "📊 *All Categories Stock Summary:*\n\n"
        for key, category in INVENTORY.items():
            available = sum(1 for item in category["items"] if "✅" in item or "⚠️" in item)
            total = len(category["items"])
            message += f"• {category['name']}: {available}/{total} items available\n"
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message, 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    if query.data == "back_to_menu":
        # Return to main menu
        await start(update, context)
        return
    
    # Handle category selection
    category_info = INVENTORY.get(query.data)
    
    if category_info:
        # Format the stock list with emojis
        stock_list = "\n".join(category_info["items"])
        
        message = (
            f"📦 *{category_info['name']} - Live Stock:*\n"
            f"{'─' * 30}\n"
            f"{stock_list}\n"
            f"{'─' * 30}\n\n"
            "💡 *How to purchase:*\n"
            "1️⃣ Click /purchase [gift card name]\n"
            "2️⃣ Or contact @GiftmartSupport\n\n"
            "🔄 *Need help?* Use /help"
        )
        
        # Add back button
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message, 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Category not found. Please use /start to return to main menu.",
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = (
        "🤖 *Giftmart Bot Help*\n\n"
        "📋 *Available Commands:*\n"
        "• /start - Open main catalog with menu buttons\n"
        "• /help - Show this help message\n"
        "• /stock - Check all categories stock summary\n"
        "• /purchase [item] - Purchase a gift card (coming soon)\n\n"
        "📱 *How to use:*\n"
        "1. Click /start to open the menu\n"
        "2. Select a category to view available gift cards\n"
        "3. Check stock status and pricing\n"
        "4. Contact support to purchase\n\n"
        "❓ For support: @GiftmartSupport"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all categories with stock status."""
    message = "📊 *All Categories Stock Status:*\n\n"
    
    for key, category in INVENTORY.items():
        available = sum(1 for item in category["items"] if "✅" in item)
        low_stock = sum(1 for item in category["items"] if "⚠️" in item)
        out_of_stock = sum(1 for item in category["items"] if "❌" in item)
        
        message += f"*{category['name']}*\n"
        message += f"✅ Available: {available} | ⚠️ Low: {low_stock} | ❌ Out: {out_of_stock}\n\n"
    
    message += "🔄 Type /start to browse categories with interactive buttons."
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def purchase_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle purchase requests."""
    if context.args:
        item_name = " ".join(context.args)
        message = (
            f"🛒 *Purchase Request*\n\n"
            f"Item: *{item_name}*\n"
            f"Status: ⏳ Processing...\n\n"
            f"📞 Please contact @GiftmartSupport to complete your purchase.\n"
            f"💳 Payment methods: Bitcoin, PayPal, Credit Card"
        )
    else:
        message = (
            "🛒 *How to Purchase*\n\n"
            "To purchase a gift card, use:\n"
            "`/purchase [gift card name]`\n\n"
            "Example: `/purchase PlayStation Store $10`\n\n"
            "Or contact @GiftmartSupport directly."
        )
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def start_with_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle start command when editing messages."""
    query = update.callback_query
    await query.answer()
    await start(update, context)

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
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("purchase", purchase_command))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start polling
    logger.info("✅ Bot is running and listening for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
