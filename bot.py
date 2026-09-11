import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Data file paths
USERS_FILE = "users.json"

# Data management functions
def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    return load_data(USERS_FILE)

def save_users(users):
    save_data(USERS_FILE, users)

# Main catalog message
CATALOG_MESSAGE = """🏨 *BOOK CHEAP HOTELS ONLINE. NO RESERVATION COSTS. GREAT RATES. SAVE 50% WITH GENIUS.* 🏨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✈️ *AIRLINES / FLIGHTS*
• Delta Gift Cards
• American Airlines Gift Cards
• Norwegian Airlines Gift Cards
• British Airways Gift Cards
• Alaska Airlines Gift Cards
• Hawaiian Airlines Gift Cards
• Virgin Atlantic Gift Cards
• Pegasus Airlines Gift Cards
*+300 More…*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 *AIRBNB & HOTELS*
• Airbnb Gift Cards
• Roomcard Gift Cards
• Hotels.com Gift Cards
• Hotelgift Gift Cards
• Hilton Hotels Gift Cards
• Choice Hotels Gift Cards
• Mr. and Mrs. Smith Gift Cards
• Four Seasons Hotels Gift Cards
• Kimpton Hotels & Restaurants Gift Cards
*+100 More…*

📚 *202 Methods*
• 2026 Methods and Tutorials

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛍️ *SHOPPING STORES*
• Nikes Gift Cards
• Adidas Gift Cards
• Cotton.on Gift Cards
• BestBuy Gift Cards
• Walmart Gift Cards
*And Many More…*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 *MORE GIFT CARDS*
• Visa Gift Card
• Amazon Gift Card
• American Express Gift Card
• iTunes Gift Card
• Walmart Gift Card
• Target Gift Card
• Starbucks Gift Card
• Netflix Gift Card
• eBay Gift Card
• Google Play Gift Card
• MasterCard Gift Card
• Disney Gift Card
• Macy's Gift Card
• Best Buy Gift Card
• Sephora Gift Card
• Home Depot Gift Card
• McDonald's Gift Card
• Costco Gift Card
• Chipotle Gift Card
• Etsy Gift Card
• Lowe's Gift Card
• Ikea Gift Card
• Gamestop Gift Card
• Nordstrom Gift Card
• Whole Foods Gift Card
• Apple Store Gift Card
• H&M Gift Card
• Subway Gift Card
• Nike Gift Card
• Olive Garden Gift Card
• Rei Gift Card
• Shell Gift Card
• T.J. Maxx Gift Card
• Red Lobster Gift Card
• Victoria's Secret Gift Card
• Old Navy Gift Card
• Pizza Hut Gift Card
• Sears Gift Card
• Cotton.on Gift Card
• Uber Gift Card
• Apple Gift Cards
• Tickets Master Gift Cards
• T-Mobile Gift Card and Refill
• Cricket Gift Cards
• Verizon Gift Card
*And Others…*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 *BOOKINGS*
• AirBnB & Hotels
• Airlines
• Car Rentals

💰 *RATE*
🌐 50% Off Discount

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛒 *How to Order:*
Click the button below to browse categories or contact support!"""

# Channel link message
CHANNEL_MESSAGE = """📢 *JOIN OUR OFFICIAL CHANNEL*

Get exclusive deals, updates, and gift card drops before anyone else!

👇 Click below to join:

https://t.me/+LsdZ3yOo8XFjMzhk

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛒 *Browse our catalog:* /start
❓ *Need help?* /help"""

# Contact admin message
CONTACT_MESSAGE = """👤 *CONTACT ADMIN*

Have questions or want to place an order?

📩 *Message Admin:* @Rt3458uy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 Our team responds within minutes!

🛒 *Browse catalog:* /start
📢 *Join channel:* [Click Here](https://t.me/+LsdZ3yOo8XFjMzhk)"""

# Main menu keyboard
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("✈️ Airlines / Flights", callback_data="category_airlines")],
        [InlineKeyboardButton("🏠 Airbnb & Hotels", callback_data="category_hotels")],
        [InlineKeyboardButton("🛍️ Shopping Stores", callback_data="category_shopping")],
        [InlineKeyboardButton("💳 All Gift Cards", callback_data="category_giftcards")],
        [InlineKeyboardButton("📚 202 Methods", callback_data="category_methods")],
        [InlineKeyboardButton("💰 50% Off Deals", callback_data="category_deals")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+LsdZ3yOo8XFjMzhk")],
        [InlineKeyboardButton("👤 Contact Admin", url="https://t.me/Rt3458uy")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Category details
CATEGORIES = {
    "airlines": {
        "name": "✈️ Airlines / Flights",
        "items": [
            "Delta Gift Cards",
            "American Airlines Gift Cards",
            "Norwegian Airlines Gift Cards",
            "British Airways Gift Cards",
            "Alaska Airlines Gift Cards",
            "Hawaiian Airlines Gift Cards",
            "Virgin Atlantic Gift Cards",
            "Pegasus Airlines Gift Cards",
            "+300 More…"
        ]
    },
    "hotels": {
        "name": "🏠 Airbnb & Hotels",
        "items": [
            "Airbnb Gift Cards",
            "Roomcard Gift Cards",
            "Hotels.com Gift Cards",
            "Hotelgift Gift Cards",
            "Hilton Hotels Gift Cards",
            "Choice Hotels Gift Cards",
            "Mr. and Mrs. Smith Gift Cards",
            "Four Seasons Hotels Gift Cards",
            "Kimpton Hotels & Restaurants Gift Cards",
            "+100 More…"
        ]
    },
    "shopping": {
        "name": "🛍️ Shopping Stores",
        "items": [
            "Nikes Gift Cards",
            "Adidas Gift Cards",
            "Cotton.on Gift Cards",
            "BestBuy Gift Cards",
            "Walmart Gift Cards",
            "And Many More…"
        ]
    },
    "giftcards": {
        "name": "💳 All Gift Cards",
        "items": [
            "Visa Gift Card", "Amazon Gift Card", "American Express Gift Card",
            "iTunes Gift Card", "Walmart Gift Card", "Target Gift Card",
            "Starbucks Gift Card", "Netflix Gift Card", "eBay Gift Card",
            "Google Play Gift Card", "MasterCard Gift Card", "Disney Gift Card",
            "Macy's Gift Card", "Best Buy Gift Card", "Sephora Gift Card",
            "Home Depot Gift Card", "McDonald's Gift Card", "Costco Gift Card",
            "Chipotle Gift Card", "Etsy Gift Card", "Lowe's Gift Card",
            "Ikea Gift Card", "Gamestop Gift Card", "Nordstrom Gift Card",
            "Whole Foods Gift Card", "Apple Store Gift Card", "H&M Gift Card",
            "Subway Gift Card", "Nike Gift Card", "Olive Garden Gift Card",
            "Rei Gift Card", "Shell Gift Card", "T.J. Maxx Gift Card",
            "Red Lobster Gift Card", "Victoria's Secret Gift Card",
            "Old Navy Gift Card", "Pizza Hut Gift Card", "Sears Gift Card",
            "Cotton.on Gift Card", "Uber Gift Card", "Apple Gift Cards",
            "Tickets Master Gift Cards", "T-Mobile Gift Card and Refill",
            "Cricket Gift Cards", "Verizon Gift Card", "And Others…"
        ]
    },
    "methods": {
        "name": "📚 202 Methods",
        "items": [
            "2026 Methods and Tutorials",
            "Premium Methods Available",
            "Contact admin for full list"
        ]
    },
    "deals": {
        "name": "💰 50% Off Deals",
        "items": [
            "🌐 50% Off Discount on all gift cards",
            "No reservation costs",
            "Great rates guaranteed",
            "Save 50% with Genius"
        ]
    }
}

# Send initial messages sequence (2 min delays)
async def send_initial_messages(chat_id, context):
    """Send the initial 3 messages with 2-minute delays"""
    try:
        # Wait 2 minutes, then send channel link
        await asyncio.sleep(120)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=CHANNEL_MESSAGE,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
        except Exception as e:
            logger.error(f"Error sending channel message to {chat_id}: {e}")
        
        # Wait 2 more minutes, then send contact info
        await asyncio.sleep(120)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=CONTACT_MESSAGE,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error sending contact message to {chat_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in send_initial_messages: {e}")

# Hourly reminder function - sends to ALL users
async def send_hourly_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send hourly reminder to ALL subscribed users"""
    try:
        users = load_users()
        
        if not users:
            logger.info("No users to remind yet")
            return
        
        success_count = 0
        fail_count = 0
        
        for user_id, user_data in users.items():
            try:
                # Send the main catalog message with buttons
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=CATALOG_MESSAGE,
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard()
                )
                
                # Update last reminder time
                user_data['last_reminder'] = datetime.now().isoformat()
                user_data['reminders_received'] = user_data.get('reminders_received', 0) + 1
                success_count += 1
                
                # Small delay between messages to avoid flood limits
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error sending reminder to {user_id}: {e}")
                fail_count += 1
                # Mark user as inactive if blocked
                if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                    user_data['is_active'] = False
                    user_data['blocked_at'] = datetime.now().isoformat()
        
        save_users(users)
        logger.info(f"✅ Hourly reminders sent: {success_count} success, {fail_count} failed")
        
    except Exception as e:
        logger.error(f"Error in hourly reminder: {e}")

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and catalog"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    
    # Register user for reminders
    users = load_users()
    is_new_user = user_id not in users
    
    if is_new_user:
        users[user_id] = {
            "username": user.first_name or "User",
            "first_seen": datetime.now().isoformat(),
            "last_reminder": None,
            "reminders_received": 0,
            "messages_received": 1,
            "is_active": True
        }
        logger.info(f"🆕 New user registered: {user.first_name} ({user_id})")
    else:
        users[user_id]["messages_received"] = users[user_id].get("messages_received", 0) + 1
        users[user_id]["is_active"] = True
        users[user_id]["username"] = user.first_name or "User"
    
    save_users(users)
    
    # Send main catalog message with buttons
    await update.message.reply_text(
        CATALOG_MESSAGE,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Start the delayed messages sequence (only for new users)
    if is_new_user:
        context.application.create_task(
            send_initial_messages(chat_id, context)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    help_text = (
        "🆘 *Giftmart Help*\n\n"
        "📋 *Commands:*\n"
        "• /start - View catalog\n"
        "• /help - This menu\n"
        "• /categories - Browse categories\n"
        "• /contact - Contact admin\n"
        "• /channel - Join our channel\n"
        "• /stop - Stop hourly reminders\n"
        "• /resume - Resume hourly reminders\n\n"
        "🛒 *How to Order:*\n"
        "1. Browse our catalog\n"
        "2. Choose your gift card\n"
        "3. Contact @Rt3458uy to order\n\n"
        "💰 *Discounts:*\n"
        "🌐 50% Off on all gift cards\n\n"
        "📢 *Join Channel:*\n"
        "https://t.me/+LsdZ3yOo8XFjMzhk\n\n"
        "👤 *Contact Admin:*\n"
        "@Rt3458uy"
    )
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all categories"""
    keyboard = [
        [InlineKeyboardButton("✈️ Airlines / Flights", callback_data="category_airlines")],
        [InlineKeyboardButton("🏠 Airbnb & Hotels", callback_data="category_hotels")],
        [InlineKeyboardButton("🛍️ Shopping Stores", callback_data="category_shopping")],
        [InlineKeyboardButton("💳 All Gift Cards", callback_data="category_giftcards")],
        [InlineKeyboardButton("📚 202 Methods", callback_data="category_methods")],
        [InlineKeyboardButton("💰 50% Off Deals", callback_data="category_deals")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📂 *Browse Categories*\n\nSelect a category to view available gift cards:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send contact information"""
    await update.message.reply_text(
        CONTACT_MESSAGE,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send channel link"""
    await update.message.reply_text(
        CHANNEL_MESSAGE,
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop hourly reminders"""
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id in users:
        users[user_id]["is_active"] = False
        users[user_id]["stopped_at"] = datetime.now().isoformat()
        save_users(users)
        await update.message.reply_text(
            "🔕 *Reminders stopped!*\n\n"
            "You will no longer receive hourly updates.\n\n"
            "To resume, use /resume",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ *You are not registered!*\n\nUse /start to register.",
            parse_mode="Markdown"
        )

async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume hourly reminders"""
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id in users:
        users[user_id]["is_active"] = True
        users[user_id]["resumed_at"] = datetime.now().isoformat()
        save_users(users)
        await update.message.reply_text(
            "🔔 *Reminders resumed!*\n\n"
            "You will now receive hourly updates again.\n\n"
            "To stop, use /stop",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ *You are not registered!*\n\nUse /start to register.",
            parse_mode="Markdown"
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics (admin only - add your user ID)"""
    ADMIN_IDS = [123456789]  # Replace with your Telegram user ID
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "❌ *Access denied!*\n\nThis command is for admins only.",
            parse_mode="Markdown"
        )
        return
    
    users = load_users()
    active_users = [u for u in users.values() if u.get("is_active", True)]
    
    stats_text = (
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: {len(users)}\n"
        f"✅ Active Users: {len(active_users)}\n"
        f"🔕 Stopped: {len(users) - len(active_users)}\n\n"
        f"🕐 Hourly reminders are running"
    )
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_menu":
        await query.edit_message_text(
            CATALOG_MESSAGE,
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    if query.data.startswith("category_"):
        category_key = query.data.replace("category_", "")
        category = CATEGORIES.get(category_key)
        
        if not category:
            await query.edit_message_text(
                "❌ Category not found!",
                parse_mode="Markdown"
            )
            return
        
        # Format category items
        items_text = "\n".join([f"• {item}" for item in category["items"]])
        
        message = (
            f"*{category['name']}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{items_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 *50% Off on all items!*\n\n"
            f"🛒 *To order:* Contact @Rt3458uy"
        )
        
        keyboard = [
            [InlineKeyboardButton("👤 Contact Admin", url="https://t.me/Rt3458uy")],
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+LsdZ3yOo8XFjMzhk")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Start the bot"""
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
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(CommandHandler("channel", channel_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("resume", resume_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Add button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Schedule hourly reminders to ALL subscribed users
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_hourly_reminder,
        interval=3600,  # 1 hour = 3600 seconds
        first=10  # Start 10 seconds after bot starts
    )
    
    # Start polling
    logger.info("✅ Bot is running with hourly reminders every 1 hour...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
