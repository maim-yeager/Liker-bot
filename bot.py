import asyncio
import os
import logging
from datetime import datetime, timedelta
import sys

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import with error handling
try:
    from aiogram import Bot, Dispatcher
    from aiogram.enums import ParseMode
    from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.filters import Command
    from aiogram.client.default import DefaultBotProperties
    import aiohttp
except ImportError as e:
    logger.error(f"Failed to import dependencies: {e}")
    logger.info("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Configuration
API_TOKEN = os.getenv("BOT_TOKEN", "8716756099:AAE9PowncF7tuYFHK1AEzhC-AFL_Bp5RTE0")
ALLOWED_GROUP_ID = -1003854531903
VIP_USER_ID = 6375918223
ADMIN_USER_ID = 6375918223

# Initialize bot
try:
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    sys.exit(1)

# Storage
user_usage = {}
like_usage = {"BD": 0, "IND": 0}
bot_start_time = datetime.now()

def join_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url="https://t.me/xpm_like_bot")],
    ])

def vip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url="https://t.me/xpm_like_bot")],
        [InlineKeyboardButton(text="💎 Buy VIP", url="https://t.me/@xr_maim")],
    ])

def verify_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Verify For Extra Likes", url="https://shortxlinks.in/RTubx")],
    ])

def reset_daily_limits():
    global user_usage, like_usage
    user_usage.clear()
    like_usage = {"BD": 0, "IND": 0}
    logger.info("✅ Daily limits reset.")
    return f"✅ Daily limits reset at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

async def send_bot_status():
    """Send bot status to admin"""
    uptime = datetime.now() - bot_start_time
    status_text = (
        f"🤖 Bot Status Report\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✅ Status: Online\n"
        f"⏱️ Uptime: {str(uptime).split('.')[0]}\n"
        f"📅 Started: {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📊 Today's Stats:\n"
        f"🇧🇩 BD Likes: {like_usage['BD']}/30\n"
        f"🇮🇳 IND Likes: {like_usage['IND']}/30\n"
        f"👥 Active Users: {len(user_usage)}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💡 Use /stats for detailed info"
    )
    try:
        await bot.send_message(ADMIN_USER_ID, status_text)
    except Exception as e:
        logger.error(f"Failed to send status: {e}")

async def daily_reset_scheduler():
    """Reset limits at midnight and send report"""
    while True:
        try:
            now = datetime.now()
            next_reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            wait_seconds = (next_reset - now).total_seconds()
            logger.info(f"Next reset in {wait_seconds/3600:.2f} hours")
            await asyncio.sleep(wait_seconds)
            
            # Reset limits and get report
            report = reset_daily_limits()
            
            # Send daily report to admin
            try:
                await bot.send_message(
                    ADMIN_USER_ID,
                    f"📊 Daily Report\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"{report}\n"
                    f"Yesterday's Total:\n"
                    f"🇧🇩 BD: {like_usage['BD']} likes\n"
                    f"🇮🇳 IND: {like_usage['IND']} likes\n"
                    f"👥 Users: {len(user_usage)}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"New day started! Users can use /like again."
                )
            except Exception as e:
                logger.error(f"Failed to send daily report: {e}")
        except Exception as e:
            logger.error(f"Error in daily reset scheduler: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

async def fetch_json(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"API returned status {r.status}")
    except asyncio.TimeoutError:
        logger.error("API request timed out")
    except Exception as e:
        logger.error(f"Error fetching JSON: {e}")
    return None

def check_permission(func):
    """Check if user is allowed to use the bot"""
    async def wrapper(msg: Message):
        user_id = msg.from_user.id
        
        # Allow admin and VIP to use bot anywhere
        if user_id in [ADMIN_USER_ID, VIP_USER_ID]:
            return await func(msg)
        
        # Check if in allowed group
        if msg.chat.id != ALLOWED_GROUP_ID:
            logger.warning(f"Unauthorized access from user {user_id} in chat {msg.chat.id}")
            
            # Inform user they need to join the group
            await msg.reply(
                "❌ <b>Access Denied!</b>\n\n"
                "This bot is only available in our official group.\n\n"
                "👉 <b>Join our group to use the bot:</b>\n"
                "https://t.me/xpm_like_bot\n\n"
                "After joining, use the bot there!",
                reply_markup=join_keyboard()
            )
            return
        
        return await func(msg)
    return wrapper

@dp.message(Command("start"))
async def start_handler(msg: Message):
    welcome_text = (
        "🤖 <b>MAIM Like Bot</b>\n\n"
        "Welcome to the ultimate like bot!\n\n"
        "<b>📌 Commands:</b>\n"
        "• /like bd uid - Send likes to BD region\n"
        "• /like ind uid - Send likes to IND region\n"
        "• /stats - Check bot statistics\n"
        "• /help - Show this message\n\n"
        "<b>⭐ Features:</b>\n"
        "• Free 1 like per day per user\n"
        "• 30 likes total per region daily\n"
        "• VIP users get unlimited access\n"
        "• Auto-reset at midnight\n\n"
        "<b>💡 Pro Tip:</b>\n"
        "Join our channel for updates and VIP offers!"
    )
    
    # Show group link to non-VIP users
    if msg.from_user.id not in [ADMIN_USER_ID, VIP_USER_ID]:
        welcome_text += "\n\n⚠️ <b>Note:</b> Bot works only in our official group!"
    
    await msg.reply(welcome_text, reply_markup=join_keyboard())
    logger.info(f"User {msg.from_user.id} started the bot")

@dp.message(Command("help"))
async def help_handler(msg: Message):
    help_text = (
        "📖 <b>Help Guide</b>\n\n"
        "<b>How to use:</b>\n"
        "1️⃣ /like bd [UID] - Send likes to Bangladesh server\n"
        "2️⃣ /like ind [UID] - Send likes to India server\n\n"
        "<b>Example:</b>\n"
        "/like bd 123456789\n\n"
        "<b>Limits:</b>\n"
        "• Regular users: 1 like/day\n"
        "• VIP users: Unlimited\n"
        "• Regional limit: 30 likes/day\n\n"
        "<b>Where to use:</b>\n"
        "• Bot works in our official group only\n"
        "• Join: https://t.me/xpm_like_bot\n\n"
        "<b>Need help?</b>\n"
        "Contact: @xr_maim"
    )
    await msg.reply(help_text, reply_markup=join_keyboard())

@dp.message(Command("stats"))
async def stats_handler(msg: Message):
    uptime = datetime.now() - bot_start_time
    is_vip = (msg.from_user.id == VIP_USER_ID)
    is_admin = (msg.from_user.id == ADMIN_USER_ID)
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <b>Uptime:</b> {str(uptime).split('.')[0]}\n"
        f"👥 <b>Active Users Today:</b> {len(user_usage)}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Today's Likes:</b>\n"
        f"🇧🇩 <b>BD Region:</b> {like_usage['BD']}/30\n"
        f"🇮🇳 <b>IND Region:</b> {like_usage['IND']}/30\n"
        f"━━━━━━━━━━━━━━━━━\n"
    )
    
    if is_vip or is_admin:
        stats_text += "👑 <b>VIP Status:</b> ✅ You are VIP! Unlimited likes\n"
    else:
        stats_text += "👑 <b>VIP Status:</b> ❌ Regular User (1 like/day)\n"
        stats_text += "💎 <b>Upgrade to VIP</b> for unlimited access!\n"
    
    stats_text += "━━━━━━━━━━━━━━━━━\n🔄 Resets at midnight daily"
    
    await msg.reply(stats_text, reply_markup=join_keyboard())

@dp.message(Command("like"))
@check_permission  # Use the new permission checker
async def like_handler(msg: Message):
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.reply(
            "❗ <b>Invalid format!</b>\n\n"
            "Correct usage:\n"
            "/like bd [UID]\n"
            "/like ind [UID]\n\n"
            "<b>Example:</b>\n"
            "/like bd 123456789",
            reply_markup=join_keyboard()
        )
        return
    
    region, uid = parts[1].upper(), parts[2]
    if region not in ["BD", "IND"]:
        await msg.reply(
            "❗ <b>Invalid region!</b>\n\n"
            "Supported regions:\n"
            "🇧🇩 BD - Bangladesh\n"
            "🇮🇳 IND - India",
            reply_markup=join_keyboard()
        )
        return

    user_id = msg.from_user.id
    is_vip = (user_id == VIP_USER_ID)
    
    # Check user limit
    if not is_vip:
        count = user_usage.get(user_id, {}).get("like", 0)
        if count >= 1:
            await msg.reply(
                "🚫 <b>Daily Limit Reached!</b>\n\n"
                f"You have used your 1 like for today.\n"
                f"Try again tomorrow or become VIP for unlimited likes!\n\n"
                f"💎 <b>VIP Benefits:</b>\n"
                f"• Unlimited likes\n"
                f"• Priority support\n"
                f"• No daily limits",
                reply_markup=vip_keyboard()
            )
            return

    # Check regional limit
    if like_usage[region] >= 30 and not is_vip:
        await msg.reply(
            f"⚠️ <b>Daily Limit Reached for {region}!</b>\n\n"
            f"Total likes sent today: {like_usage[region]}/30\n"
            f"Please try again tomorrow.\n\n"
            f"💎 <b>VIP users</b> can bypass this limit!\n"
            f"Contact @xr_maim to upgrade.",
            reply_markup=vip_keyboard()
        )
        return

    # Send likes
    wait_msg = await msg.reply("⏳ <b>Sending Likes...</b>\n\nPlease wait while we process your request.")
    
    url = f"https://anish-likes.vercel.app/like?server_name={region.lower()}&uid={uid}&key=jex4rrr"
    data = await fetch_json(url)

    if not data:
        await wait_msg.edit_text(
            "❌ <b>Connection Error!</b>\n\n"
            "Failed to connect to API server.\n"
            "Please try again in a few minutes.\n\n"
            "If problem persists, contact @xr_maim",
            reply_markup=join_keyboard()
        )
        return

    if data.get("status") == 2:
        await wait_msg.edit_text(
            f"🚫 <b>Max Likes Reached for Today!</b>\n\n"
            f"👤 <b>Name:</b> {data.get('PlayerNickname', 'N/A')}\n"
            f"🆔 <b>UID:</b> {uid}\n"
            f"🌍 <b>Region:</b> {region}\n"
            f"❤️ <b>Current Likes:</b> {data.get('LikesNow', 'N/A')}\n\n"
            f"💡 <b>Tip:</b> Try again tomorrow or use a different account!",
            reply_markup=vip_keyboard()
        )
        return

    # Success message
    success_text = (
        f"✅ <b>Likes Sent Successfully!</b>\n\n"
        f"👤 <b>Name:</b> {data.get('PlayerNickname', 'N/A')}\n"
        f"🆔 <b>UID:</b> {uid}\n"
        f"🌍 <b>Region:</b> {region}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"❤️ <b>Before:</b> {data.get('LikesbeforeCommand', 'N/A')}\n"
        f"👍 <b>After:</b> {data.get('LikesafterCommand', 'N/A')}\n"
        f"🎯 <b>Sent:</b> {data.get('LikesGivenByAPI', 'N/A')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📢 Join @xpm_like_bot for more!"
    )
    await wait_msg.edit_text(success_text, reply_markup=join_keyboard())

    # Update usage
    if not is_vip:
        if user_id not in user_usage:
            user_usage[user_id] = {}
        user_usage[user_id]["like"] = 1
        like_usage[region] += 1
        logger.info(f"User {user_id} used like in {region}. Total: {like_usage[region]}")
    else:
        logger.info(f"VIP user {user_id} used like in {region}")

@dp.message()
async def handle_other_messages(msg: Message):
    # Only respond in allowed group for non-VIP users
    if msg.from_user.id in [ADMIN_USER_ID, VIP_USER_ID]:
        await msg.reply(
            "🤖 <b>Unknown Command</b>\n\n"
            "Use these commands:\n"
            "• /like bd uid - Send likes\n"
            "• /like ind uid - Send likes\n"
            "• /stats - View statistics\n"
            "• /help - Get help",
            reply_markup=join_keyboard()
        )
    elif msg.chat.id == ALLOWED_GROUP_ID:
        await msg.reply(
            "🤖 <b>Unknown Command</b>\n\n"
            "Use these commands:\n"
            "• /like bd uid - Send likes\n"
            "• /like ind uid - Send likes\n"
            "• /stats - View statistics\n"
            "• /help - Get help",
            reply_markup=join_keyboard()
        )

@dp.message(Command("admin"))
async def admin_handler(msg: Message):
    if msg.from_user.id == ADMIN_USER_ID:
        uptime = datetime.now() - bot_start_time
        admin_text = (
            f"🔧 <b>Admin Panel</b>\n\n"
            f"📊 <b>Bot Status:</b> ✅ Online\n"
            f"⏱️ <b>Uptime:</b> {str(uptime).split('.')[0]}\n"
            f"👥 <b>Active Users:</b> {len(user_usage)}\n"
            f"📈 <b>BD Likes:</b> {like_usage['BD']}/30\n"
            f"📈 <b>IND Likes:</b> {like_usage['IND']}/30\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>Commands:</b>\n"
            f"• /send_status - Send status to admin\n"
            f"• /reset_limits - Force reset limits"
        )
        await msg.reply(admin_text)

@dp.message(Command("send_status"))
async def send_status_handler(msg: Message):
    if msg.from_user.id == ADMIN_USER_ID:
        await send_bot_status()
        await msg.reply("✅ Status sent to admin!")

@dp.message(Command("reset_limits"))
async def reset_limits_handler(msg: Message):
    if msg.from_user.id == ADMIN_USER_ID:
        report = reset_daily_limits()
        await msg.reply(f"✅ {report}")

async def on_startup():
    """Actions when bot starts"""
    logger.info("🤖 MAIM AI Like Bot is starting...")
    
    # Send startup message to admin
    startup_text = (
        f"🚀 <b>Bot Started Successfully!</b>\n\n"
        f"📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"👤 <b>Bot ID:</b> {bot.id}\n"
        f"🔧 <b>Mode:</b> Polling\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✅ All systems operational\n"
        f"✅ Daily limits initialized\n"
        f"✅ Ready to accept commands"
    )
    try:
        await bot.send_message(ADMIN_USER_ID, startup_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def main():
    try:
        # Setup
        await on_startup()
        
        # Start scheduler
        asyncio.create_task(daily_reset_scheduler())
        
        # Remove webhook and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting polling...")
        
        # Send periodic status every 6 hours
        async def periodic_status():
            while True:
                await asyncio.sleep(21600)  # 6 hours
                await send_bot_status()
        
        asyncio.create_task(periodic_status())
        
        # Start bot
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
