import os
import logging
import tempfile
import shutil
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import imageio
import numpy as np
from moviepy.editor import VideoFileClip
import zipfile

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ensure temp directory exists
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# User session storage (simple in-memory)
user_sessions = {}

# Helper Functions
def cleanup_temp_files(file_path):
    """Remove temporary files"""
    try:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                os.remove(file_path)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def video_to_gif(video_path, output_path, fps=10, max_frames=100):
    """Convert video to GIF using moviepy and imageio"""
    try:
        # Load video
        clip = VideoFileClip(video_path)
        
        # Reduce duration if too long (max 60 seconds)
        if clip.duration > 60:
            clip = clip.subclip(0, 60)
        
        # Resize if too large (max 480p)
        if clip.size[0] > 480 or clip.size[1] > 480:
            clip = clip.resize(height=480)
        
        # Extract frames
        frames = []
        frame_count = min(int(clip.duration * fps), max_frames)
        
        for t in range(frame_count):
            frame = clip.get_frame(t / fps)
            frames.append(frame)
        
        clip.close()
        
        if not frames:
            return None, "No frames extracted from video"
        
        # Convert to uint8
        frames = [np.array(frame, dtype=np.uint8) for frame in frames]
        
        # Save as GIF
        imageio.mimsave(output_path, frames, fps=fps)
        
        return output_path, None
    except Exception as e:
        logger.error(f"Video to GIF error: {e}")
        return None, str(e)

def gif_to_frames(gif_path, output_dir, format="png", max_frames=50):
    """Extract frames from GIF to images"""
    try:
        gif = Image.open(gif_path)
        frames = []
        
        # Limit to max_frames
        total_frames = min(gif.n_frames, max_frames)
        
        for frame_idx in range(total_frames):
            gif.seek(frame_idx)
            frame = gif.copy()
            
            # Convert to RGB if needed
            if frame.mode != 'RGB':
                frame = frame.convert('RGB')
            
            frame_path = os.path.join(output_dir, f"frame_{frame_idx+1:03d}.{format}")
            frame.save(frame_path, format.upper())
            frames.append(frame_path)
        
        gif.close()
        return frames, None
    except Exception as e:
        logger.error(f"GIF to frames error: {e}")
        return None, str(e)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    user = update.effective_user
    
    welcome_text = (
        f"🎬 *Hi {user.first_name}! Welcome to Media Converter Bot!*\n\n"
        f"I can convert:\n"
        f"🎥 Video → GIF\n"
        f"🎞️ GIF → Images\n\n"
        f"*How to use:*\n"
        f"1. Send me a video or GIF file\n"
        f"2. Choose your conversion option\n"
        f"3. Wait for the magic! ✨\n\n"
        f"⚠️ *Limits:*\n"
        f"• Max file size: 50MB\n"
        f"• Video length: Max 60 seconds\n"
        f"• GIF frames: Max 50\n\n"
        f"🔄 *Commands:*\n"
        f"/start - Show this menu\n"
        f"/help - More details\n"
        f"/cancel - Cancel current operation"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎥 Convert Video to GIF", callback_data="video_to_gif")],
        [InlineKeyboardButton("🎞️ Convert GIF to Images", callback_data="gif_to_images")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming video or GIF files"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Check if it's a video or GIF
    document = update.message.document
    video = update.message.video
    animation = update.message.animation
    
    file_obj = None
    file_type = None
    file_name = None
    mime_type = None
    
    if document:
        file_name = document.file_name or "file"
        mime_type = document.mime_type or ""
        if file_name.lower().endswith(('.gif', '.mp4', '.avi', '.mov', '.mkv', '.webm')) or 'video' in mime_type:
            file_obj = document
            file_type = "document"
    elif video:
        file_obj = video
        file_type = "video"
        file_name = f"{user_id}_video.mp4"
    elif animation:
        file_obj = animation
        file_type = "gif"
        file_name = f"{user_id}_animation.gif"
    else:
        await update.message.reply_text(
            "❌ Please send a video file (MP4, AVI, MOV, MKV, WEBM) or GIF.\n\n"
            "I support most video formats and animated GIFs!"
        )
        return
    
    # Check file size (50MB limit)
    if file_obj.file_size > 50 * 1024 * 1024:
        await update.message.reply_text(
            "❌ File is too large! Maximum size is 50MB.\n"
            "Please compress your file and try again."
        )
        return
    
    # Store file info in user session
    user_sessions[user_id] = {
        "file_id": file_obj.file_id,
        "file_type": file_type,
        "file_name": file_name,
        "file_size": file_obj.file_size
    }
    
    # Show conversion options
    keyboard = []
    if file_type in ["video", "document"]:
        keyboard.append([InlineKeyboardButton("🎥 Convert to GIF", callback_data="convert_to_gif")])
    elif file_type == "gif":
        keyboard.append([InlineKeyboardButton("🎞️ Extract Frames to Images", callback_data="convert_to_images")])
    
    keyboard.append([InlineKeyboardButton("🔄 Cancel", callback_data="cancel")])
    
    await update.message.reply_text(
        f"📥 *File received!*\n\n"
        f"📁 Name: {file_name}\n"
        f"📊 Size: {file_obj.file_size / (1024 * 1024):.2f} MB\n"
        f"🔢 Type: {file_type.upper()}\n\n"
        f"What would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    if query.data == "video_to_gif":
        await query.edit_message_text(
            "📤 *Send me a video file!*\n\n"
            "Supported formats:\n"
            "• MP4\n"
            "• AVI\n"
            "• MOV\n"
            "• MKV\n"
            "• WEBM\n\n"
            "I'll convert it to a GIF for you! 🎬➡️🎞️",
            parse_mode="Markdown"
        )
        return
    
    elif query.data == "gif_to_images":
        await query.edit_message_text(
            "📤 *Send me a GIF file!*\n\n"
            "I'll extract all frames as images for you! 🎞️➡️🖼️\n\n"
            "✨ *Tip:* For better quality, send large GIF files.",
            parse_mode="Markdown"
        )
        return
    
    elif query.data == "help":
        help_text = (
            "❓ *Help*\n\n"
            "🎥 *Video to GIF:*\n"
            "• Send a video file\n"
            "• Select 'Convert to GIF'\n"
            "• Receive your GIF\n\n"
            "🎞️ *GIF to Images:*\n"
            "• Send a GIF file\n"
            "• Select 'Extract Frames'\n"
            "• Receive all frames as images\n\n"
            "⚠️ *Limitations:*\n"
            "• Max file: 50MB\n"
            "• Video: Max 60 seconds\n"
            "• GIF frames: Max 50\n\n"
            "💡 *Supported formats:*\n"
            "• Videos: MP4, AVI, MOV, MKV, WEBM\n"
            "• Images: PNG, JPEG\n"
            "• GIF: Standard GIF format"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif query.data == "back_to_menu":
        await start(update, context)
        return
    
    elif query.data == "cancel":
        if user_id in user_sessions:
            del user_sessions[user_id]
        await query.edit_message_text(
            "✅ *Operation cancelled.*\n\n"
            "Send /start to begin again.",
            parse_mode="Markdown"
        )
        return
    
    elif query.data in ["convert_to_gif", "convert_to_images"]:
        if user_id not in user_sessions:
            await query.edit_message_text(
                "❌ *Session expired!*\n\n"
                "Please send the file again.",
                parse_mode="Markdown"
            )
            return
        
        file_info = user_sessions[user_id]
        file_id = file_info["file_id"]
        file_type = file_info["file_type"]
        file_name = file_info["file_name"]
        
        # Inform user about processing
        await query.edit_message_text(
            "⏳ *Processing your file...*\n\n"
            "This may take a few moments. Please wait! 🚀",
            parse_mode="Markdown"
        )
        
        try:
            # Download file
            file = await context.bot.get_file(file_id)
            
            # Create temp files
            input_path = TEMP_DIR / f"{user_id}_input"
            output_dir = TEMP_DIR / f"{user_id}_output"
            output_dir.mkdir(exist_ok=True)
            
            # Download file with proper extension
            ext = file_name.split('.')[-1] if '.' in file_name else 'file'
            input_file = TEMP_DIR / f"{user_id}_input.{ext}"
            await file.download_to_drive(input_file)
            
            if query.data == "convert_to_gif":
                # Video to GIF
                output_path = TEMP_DIR / f"{user_id}_output.gif"
                
                result, error = video_to_gif(str(input_file), str(output_path))
                if error:
                    await query.edit_message_text(
                        f"❌ *Conversion failed!*\n\n"
                        f"Error: {error[:200]}\n\n"
                        f"Please try again or contact support.",
                        parse_mode="Markdown"
                    )
                    cleanup_temp_files(str(input_file))
                    return
                
                # Send the GIF
                with open(output_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=f,
                        filename=f"{os.path.splitext(file_name)[0]}.gif",
                        caption="🎉 *Here's your GIF!* 🎉\n\nConverted from video successfully!",
                        parse_mode="Markdown"
                    )
                
                # Cleanup
                cleanup_temp_files(str(input_file))
                cleanup_temp_files(str(output_path))
                shutil.rmtree(str(output_dir), ignore_errors=True)
                if user_id in user_sessions:
                    del user_sessions[user_id]
                
                await query.edit_message_text(
                    "✅ *Conversion complete!*\n\n"
                    "🎬 Video → GIF ✅\n"
                    "📤 GIF sent successfully!\n\n"
                    "🔄 Send another file or type /start to begin again.",
                    parse_mode="Markdown"
                )
                
            elif query.data == "convert_to_images":
                # GIF to Images
                frames, error = gif_to_frames(str(input_file), str(output_dir), "png")
                if error:
                    await query.edit_message_text(
                        f"❌ *Extraction failed!*\n\n"
                        f"Error: {error[:200]}\n\n"
                        f"Please try again or contact support.",
                        parse_mode="Markdown"
                    )
                    cleanup_temp_files(str(input_file))
                    return
                
                if not frames:
                    await query.edit_message_text(
                        "❌ *No frames extracted!*\n\n"
                        "The GIF might be empty or corrupted.",
                        parse_mode="Markdown"
                    )
                    cleanup_temp_files(str(input_file))
                    return
                
                # Send frames as images (limit to 10 to avoid spam)
                for i, frame_path in enumerate(frames[:10]):
                    with open(frame_path, 'rb') as f:
                        caption = f"Frame {i+1}/{len(frames)}" if i == 0 else None
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=f,
                            caption=caption if i == 0 else None
                        )
                
                # If more than 10 frames, send as zip
                if len(frames) > 10:
                    zip_path = TEMP_DIR / f"{user_id}_frames.zip"
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for frame_path in frames:
                            zipf.write(frame_path, os.path.basename(frame_path))
                    
                    with open(zip_path, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=f,
                            filename=f"{os.path.splitext(file_name)[0]}_frames.zip",
                            caption=f"📦 *All {len(frames)} frames* in a zip file!",
                            parse_mode="Markdown"
                        )
                    
                    cleanup_temp_files(str(zip_path))
                
                # Cleanup
                cleanup_temp_files(str(input_file))
                shutil.rmtree(str(output_dir), ignore_errors=True)
                if user_id in user_sessions:
                    del user_sessions[user_id]
                
                await query.edit_message_text(
                    "✅ *Extraction complete!*\n\n"
                    "🎞️ GIF → Images ✅\n"
                    f"📤 {len(frames)} frames sent successfully!\n\n"
                    "🔄 Send another file or type /start to begin again.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            await query.edit_message_text(
                f"❌ *An error occurred!*\n\n"
                f"Error: {str(e)[:200]}\n\n"
                f"Please try again with a different file.",
                parse_mode="Markdown"
            )
            if user_id in user_sessions:
                del user_sessions[user_id]

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    help_text = (
        "🎬 *Media Converter Bot Help*\n\n"
        "📋 *Commands:*\n"
        "• /start - Start the bot\n"
        "• /help - Show this help\n"
        "• /cancel - Cancel current operation\n\n"
        "🎥 *Video → GIF:*\n"
        "1. Send a video file\n"
        "2. Click 'Convert to GIF'\n"
        "3. Receive your GIF\n\n"
        "🎞️ *GIF → Images:*\n"
        "1. Send a GIF file\n"
        "2. Click 'Extract Frames'\n"
        "3. Receive images\n\n"
        "⚡ *Tips:*\n"
        "• Smaller files process faster\n"
        "• GIF quality depends on video quality\n"
        "• PNG frames preserve best quality\n\n"
        "💬 *Support:* @YourSupportHandle"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel current operation"""
    user_id = str(update.effective_user.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text(
        "✅ *Operation cancelled.*\n\n"
        "Send /start to begin again.",
        parse_mode="Markdown"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ *An error occurred!*\n\n"
            "Please try again or contact support.\n"
            "If this persists, try using /start to begin a new session.",
            parse_mode="Markdown"
        )

def main() -> None:
    """Start the bot"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    logger.info("🚀 Starting Media Converter Bot...")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add file handler with correct filters
    application.add_handler(MessageHandler(
        filters.VIDEO | filters.ANIMATION | filters.Document.VIDEO,
        handle_file
    ))
    
    # Add button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    logger.info("✅ Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
