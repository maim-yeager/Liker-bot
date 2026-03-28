import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from environment variable (safer)
API_TOKEN = os.getenv("BOT_TOKEN", "8716756099:AAE9PowncF7tuYFHK1AEzhC-AFL_Bp5RTE0")
ALLOWED_GROUP_ID = -1003799260658
VIP_USER_ID = 6375918223

bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_usage = {}
like_usage = {"BD": 0, "IND": 0}

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
    user_usage.clear()
    like_usage["BD"] = 0
    like_usage["IND"] = 0
    logger.info("✅ Daily limits reset.")

async def daily_reset_scheduler():
    while True:
        now = datetime.now()
        next_reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        wait_seconds = (next_reset - now).total_seconds()
        logger.info(f"Next reset in {wait_seconds/3600:.2f} hours")
        await asyncio.sleep(wait_seconds)
        reset_daily_limits()

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

def group_only(func):
    async def wrapper(msg: Message):
        if msg.chat.id != ALLOWED_GROUP_ID:
            logger.warning(f"Unauthorized access from chat {msg.chat.id}")
            return
        return await func(msg)
    return wrapper

@dp.message(Command("start"))
async def start_handler(msg: Message):
    welcome_text = (
        "🤖 Welcome to MAIM Like Bot!\n\n"
        "Use /like bd <uid> to send likes to BD region\n"
        "Use /like ind <uid> to send likes to IND region\n\n"
        "VIP users get unlimited likes!"
    )
    await msg.reply(welcome_text, reply_markup=join_keyboard())

@dp.message(Command("like"))
@group_only
async def like_handler(msg: Message):
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.reply("❗ Correct format: /like bd uid\nExample: /like bd 123456789", reply_markup=join_keyboard())
        return
    
    region, uid = parts[1].upper(), parts[2]
    if region not in ["BD", "IND"]:
        await msg.reply("❗ Only BD or IND regions are supported!", reply_markup=join_keyboard())
        return

    user_id = msg.from_user.id
    if user_id != VIP_USER_ID:
        count = user_usage.get(user_id, {}).get("like", 0)
        if count >= 1:
            await msg.reply("🚫 You have already used your like command today!\n\n💡 Get VIP for unlimited likes!", reply_markup=verify_keyboard())
            return

    if like_usage[region] >= 30 and user_id != VIP_USER_ID:
        await msg.reply(
            f"⚠️ Daily like limit reached for {region} region.\n"
            f"Total likes sent today: {like_usage[region]}/30\n"
            f"Please try again tomorrow or become VIP for unlimited access!",
            reply_markup=vip_keyboard()
        )
        return

    wait = await msg.reply("⏳ Sending Likes, Please Wait.....")
    
    url = f"https://anish-likes.vercel.app/like?server_name={region.lower()}&uid={uid}&key=jex4rrr"
    data = await fetch_json(url)

    if not data:
        await wait.edit_text("❌ Failed to connect to API. Please try again later.", reply_markup=join_keyboard())
        return

    if data.get("status") == 2:
        await wait.edit_text(
            f"🚫 Max Likes Reached for Today\n\n"
            f"👤 Name: {data.get('PlayerNickname', 'N/A')}\n"
            f"🆔 UID: {uid}\n"
            f"🌍 Region: {region}\n"
            f"❤️ Current Likes: {data.get('LikesNow', 'N/A')}\n\n"
            f"💡 Tip: Try again tomorrow or use a different account!",
            reply_markup=vip_keyboard()
        )
        return

    await wait.edit_text(
        f"✅ Likes Sent Successfully!\n\n"
        f"👤 Name: {data.get('PlayerNickname', 'N/A')}\n"
        f"🆔 UID: {uid}\n"
        f"❤️ Before Likes: {data.get('LikesbeforeCommand', 'N/A')}\n"
        f"👍 Current Likes: {data.get('LikesafterCommand', 'N/A')}\n"
        f"🎯 Likes Sent: {data.get('LikesGivenByAPI', 'N/A')}\n\n"
        f"📢 Join @xpm_like_bot for more!",
        reply_markup=join_keyboard()
    )

    if user_id != VIP_USER_ID:
        user_usage.setdefault(user_id, {})["like"] = 1
        like_usage[region] += 1
        logger.info(f"User {user_id} used like in {region}. Total today: {like_usage[region]}")

@dp.message()
async def handle_other_messages(msg: Message):
    if msg.chat.id == ALLOWED_GROUP_ID:
        await msg.reply("🤖 Use /like bd <uid> or /like ind <uid> to send likes!", reply_markup=join_keyboard())

async def main():
    logger.info("🤖 MAIM AI Like Bot is starting...")
    logger.info(f"Bot will only work in group: {ALLOWED_GROUP_ID}")
    logger.info(f"VIP user: {VIP_USER_ID}")
    
    # Start the daily reset scheduler
    asyncio.create_task(daily_reset_scheduler())
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
