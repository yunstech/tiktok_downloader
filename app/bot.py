import asyncio
import httpx
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from app.config import get_settings
from app.logger import setup_logger
from app.redis_client import RedisClient

settings = get_settings()
logger = setup_logger(__name__)


class TikTokBot:
    def __init__(self):
        self.application = None
        self.redis = RedisClient()
        self.job_to_chat = {}  # Maps job_id to chat_id
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🎵 *Welcome to TikTok Scraper Bot!* 🎵\n\n"
            "I can help you download videos from any TikTok user!\n\n"
            "📝 *How to use:*\n"
            "1. Send me a TikTok username (without @)\n"
            "2. I'll scrape all videos from that profile\n"
            "3. Videos will be downloaded automatically\n"
            "4. I'll send you videos in batches of 5! 📦\n"
            "5. Use /status <job_id> to check progress\n\n"
            "💡 *Commands:*\n"
            "/start - Show this message\n"
            "/help - Get help\n"
            "/status <job_id> - Check job status\n"
            "/jobs - List all your jobs\n\n"
            "Let's get started! Send me a username 🚀"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📚 *Help & Commands*\n\n"
            "*Basic Usage:*\n"
            "Simply send me a TikTok username (e.g., 'tiktok' or 'username')\n\n"
            "*Commands:*\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/status <job_id> - Check download status\n"
            "/jobs - View all your jobs\n\n"
            "*Features:*\n"
            "• Videos sent in batches of 5 📦\n"
            "• Real-time progress updates\n"
            "• Support for large profiles\n\n"
            "*Tips:*\n"
            "• Send username without @ symbol\n"
            "• Processing may take time for large profiles\n"
            "• You'll receive videos as they're downloaded\n\n"
            "Need more help? Contact the admin!"
        )
        
        await update.message.reply_text(
            help_message,
            parse_mode="Markdown"
        )
    
    async def handle_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle username input"""
        username = update.message.text.strip().replace("@", "")
        
        # Validate username
        if not username or len(username) < 1:
            await update.message.reply_text(
                "❌ Please send a valid TikTok username!"
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            f"🔍 Searching for user: *{username}*\n"
            f"Please wait...",
            parse_mode="Markdown"
        )
        
        try:
            # Make API request to start scraping
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.api_base_url}/scrape",
                    json={"username": username},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    job_id = data["job_id"]
                    
                    # Store job_id to chat_id mapping
                    self.job_to_chat[job_id] = update.message.chat_id
                    await self.redis.client.hset("job_chat_mapping", job_id, str(update.message.chat_id))
                    
                    # Create inline keyboard
                    keyboard = [
                        [InlineKeyboardButton("📊 Check Status", callback_data=f"status_{job_id}")],
                        [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{job_id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await processing_msg.edit_text(
                        f"✅ *Job Created!*\n\n"
                        f"👤 User: `{username}`\n"
                        f"🆔 Job ID: `{job_id}`\n"
                        f"📊 Status: Pending\n\n"
                        f"I'm now scraping videos from this profile. "
                        f"This may take a few minutes depending on the number of videos.\n\n"
                        f"📹 Videos will be sent to you in batches of 5!\n\n"
                        f"Use the buttons below to check progress!",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    await processing_msg.edit_text(
                        f"❌ Failed to create job: {response.text}"
                    )
        
        except Exception as e:
            logger.error(f"Error handling username: {e}")
            await processing_msg.edit_text(
                f"❌ An error occurred: {str(e)}\n\n"
                f"Please try again later or contact support."
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a job ID!\n"
                "Usage: /status <job_id>"
            )
            return
        
        job_id = context.args[0]
        await self.send_job_status(update.message.chat_id, job_id, update.message)
    
    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /jobs command"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.api_base_url}/jobs",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    
                    if not jobs:
                        await update.message.reply_text(
                            "📭 No jobs found!\n\n"
                            "Send me a username to get started."
                        )
                        return
                    
                    message = "📋 *Your Jobs:*\n\n"
                    
                    for job in jobs[:10]:  # Limit to 10 jobs
                        message += (
                            f"👤 User: `{job['username']}`\n"
                            f"🆔 Job ID: `{job['job_id']}`\n"
                            f"📊 Status: {job['status']}\n"
                            f"📅 Created: {job.get('created_at', 'N/A')}\n\n"
                        )
                    
                    await update.message.reply_text(
                        message,
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Failed to fetch jobs: {response.text}"
                    )
        
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            await update.message.reply_text(
                f"❌ An error occurred: {str(e)}"
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data.startswith("status_") or callback_data.startswith("refresh_"):
            job_id = callback_data.split("_", 1)[1]
            await self.send_job_status(query.message.chat_id, job_id, query.message, edit=True)
    
    async def send_job_status(self, chat_id, job_id, message, edit=False):
        """Send job status to user"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.api_base_url}/job/{job_id}",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status_emoji = {
                        "pending": "⏳",
                        "scraping": "🔍",
                        "downloading": "⬇️",
                        "completed": "✅",
                        "failed": "❌"
                    }
                    
                    emoji = status_emoji.get(data["status"], "📊")
                    
                    status_text = (
                        f"{emoji} *Job Status*\n\n"
                        f"👤 User: `{data['username']}`\n"
                        f"🆔 Job ID: `{job_id}`\n"
                        f"📊 Status: *{data['status'].upper()}*\n\n"
                        f"📹 Total Videos: {data['total_videos']}\n"
                        f"✅ Downloaded: {data['downloaded_videos']}\n"
                        f"❌ Failed: {data['failed_videos']}\n\n"
                        f"🕐 Updated: {data.get('updated_at', 'N/A')}"
                    )
                    
                    # Add progress bar if downloading
                    if data['total_videos'] > 0:
                        progress = (data['downloaded_videos'] / data['total_videos']) * 100
                        bar_length = 10
                        filled = int(bar_length * progress / 100)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        status_text += f"\n\n{bar} {progress:.1f}%"
                    
                    # Create inline keyboard
                    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{job_id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    if edit:
                        await message.edit_text(
                            status_text,
                            parse_mode="Markdown",
                            reply_markup=reply_markup
                        )
                    else:
                        await message.reply_text(
                            status_text,
                            parse_mode="Markdown",
                            reply_markup=reply_markup
                        )
                
                elif response.status_code == 404:
                    await message.reply_text(
                        f"❌ Job not found: `{job_id}`",
                        parse_mode="Markdown"
                    )
                else:
                    await message.reply_text(
                        f"❌ Failed to fetch status: {response.text}"
                    )
        
        except Exception as e:
            logger.error(f"Error fetching job status: {e}")
            await message.reply_text(
                f"❌ An error occurred: {str(e)}"
            )
    
    async def send_videos_batch(self, job_id: str, chat_id: int):
        """Send a batch of videos to user"""
        try:
            # Get pending videos (up to 5)
            pending_videos = await self.redis.get_pending_videos(job_id, count=5)
            
            if not pending_videos:
                logger.info(f"No pending videos for job {job_id}")
                return
            
            logger.info(f"Sending {len(pending_videos)} videos to chat {chat_id}")
            
            # Send each video
            sent_count = 0
            skipped_count = 0
            for video_data in pending_videos:
                try:
                    video_id, filepath = video_data.split(":", 1)
                    
                    # Check if video already sent to this user
                    if await self.redis.is_video_sent(chat_id, video_id):
                        logger.info(f"Video {video_id} already sent to user {chat_id}, skipping")
                        skipped_count += 1
                        continue
                    
                    video_path = Path(filepath)
                    
                    if not video_path.exists():
                        logger.error(f"Video file not found: {filepath}")
                        continue
                    
                    # Send video to user
                    with open(video_path, 'rb') as video_file:
                        await self.application.bot.send_video(
                            chat_id=chat_id,
                            video=video_file,
                            caption=f"📹 Video ID: `{video_id}`",
                            parse_mode="Markdown",
                            supports_streaming=True,
                            read_timeout=60,
                            write_timeout=60
                        )
                    
                    # Mark video as sent
                    await self.redis.mark_video_sent(chat_id, video_id)
                    
                    sent_count += 1
                    logger.info(f"Sent video {video_id} to chat {chat_id}")
                    
                    # Small delay between sends
                    await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Failed to send video {video_id}: {e}")
                    continue
            
            # Send summary message
            if sent_count > 0 or skipped_count > 0:
                summary = f"✅ Sent {sent_count} video(s) from this batch!"
                if skipped_count > 0:
                    summary += f"\n⏭️ Skipped {skipped_count} duplicate(s)"
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=summary,
                    parse_mode="Markdown"
                )
        
        except Exception as e:
            logger.error(f"Failed to send video batch for job {job_id}: {e}")
    
    async def video_sender_worker(self):
        """Background worker to send videos"""
        logger.info("Video sender worker started")
        
        while True:
            try:
                # Check for jobs that need videos sent
                result = await self.redis.client.brpop("send_videos_queue", timeout=5)
                
                if result:
                    job_id = result[1]
                    
                    # Get chat_id for this job
                    chat_id_str = await self.redis.client.hget("job_chat_mapping", job_id)
                    
                    if chat_id_str:
                        chat_id = int(chat_id_str)
                        await self.send_videos_batch(job_id, chat_id)
                    else:
                        logger.error(f"No chat_id found for job {job_id}")
            
            except Exception as e:
                logger.error(f"Error in video sender worker: {e}")
                await asyncio.sleep(5)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    async def post_init(self, application: Application):
        """Initialize after application is created"""
        await self.redis.connect()
        # Start video sender worker
        asyncio.create_task(self.video_sender_worker())
        logger.info("Bot initialization complete")
    
    def run(self):
        """Run the bot"""
        # Create application
        self.application = Application.builder().token(settings.telegram_bot_token).post_init(self.post_init).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("jobs", self.jobs_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_username))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Start the bot
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    bot = TikTokBot()
    bot.run()


if __name__ == "__main__":
    main()
