import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebhookInfo
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta
import aiohttp
import os
from flask import Flask, request, jsonify
import threading
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = "8716756099:AAE9PowncF7tuYFHK1AEzhC-AFL_Bp5RTE0"
ALLOWED_GROUP_ID = -1003799260658
VIP_USER_ID = 6375918223

bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_usage = {}
like_usage = {"BD": 0, "IND": 0}

# Flask app for webhook
app = Flask(__name__)

# Webhook route
@app.route(f'/webhook/{API_TOKEN}', methods=['POST'])
async def webhook():
    try:
        update_data = request.get_json()
        if update_data:
            update = await dp.feed_update(bot, update_data)
            return jsonify({"status": "ok"})
        return jsonify({"status": "failed"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/')
def health_check():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return "OK", 200

@app.route('/set-webhook')
async def set_webhook():
    try:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL', 'localhost')}/webhook/{API_TOKEN}"
        await bot.set_webhook(webhook_url)
        return f"Webhook set to: {webhook_url}"
    except Exception as e:
        return f"Error: {e}"

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
        await asyncio.sleep(wait_seconds)
        reset_daily_limits()

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.json()
    return None

def group_only(func):
    async def wrapper(msg: Message):
        if msg.chat.id != ALLOWED_GROUP_ID:
            logger.info(f"Message from unauthorized chat: {msg.chat.id}")
            return
        return await func(msg)
    return wrapper

@dp.message(Command("like"))
@group_only
async def like_handler(msg: Message):
    logger.info(f"Like command received from user {msg.from_user.id} in chat {msg.chat.id}")
    
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.reply("❗ Correct format: /like bd uid", reply_markup=join_keyboard())
        return
    region, uid = parts[1].upper(), parts[2]
    if region not in ["BD", "IND"]:
        await msg.reply("❗ Only BD or IND regions are supported!", reply_markup=join_keyboard())
        return

    user_id = msg.from_user.id
    if user_id != VIP_USER_ID:
        count = user_usage.get(user_id, {}).get("like", 0)
        if count >= 1:
            await msg.reply("🚫 You have already used your like command today!", reply_markup=verify_keyboard())
            return

    if like_usage[region] >= 30 and user_id != VIP_USER_ID:
        await msg.reply(
            f"⚠️ Daily like limit reached for {region} region. Please try again tomorrow.",
            reply_markup=join_keyboard()
        )
        return

    wait = await msg.reply("⏳ Sending Likes, Please Wait.....")
    url = f"https://anish-likes.vercel.app/like?server_name={region.lower()}&uid={uid}&key=jex4rrr"
    data = await fetch_json(url)

    if not data:
        await wait.edit_text("❌ Failed to send request. Check UID or try later.", reply_markup=join_keyboard())
        return

    if data.get("status") == 2:
        await wait.edit_text(
            f"🚫 Max Likes Reached for Today\n\n"
            f"👤 Name: {data.get('PlayerNickname', 'N/A')}\n"
            f"🆔 UID: {uid}\n"
            f"🌍 Region: {region}\n"
            f"❤️ Current Likes: {data.get('LikesNow', 'N/A')}",
            reply_markup=vip_keyboard()
        )
        return

    await wait.edit_text(
        f"✅ Likes Sent Successfully!\n\n"
        f"👤 Name: {data.get('PlayerNickname', 'N/A')}\n"
        f"🆔 UID: {uid}\n"
        f"❤️ Before Likes: {data.get('LikesbeforeCommand', 'N/A')}\n"
        f"👍 Current Likes: {data.get('LikesafterCommand', 'N/A')}\n"
        f"🎯 Likes Sent By MAIM HACKER: {data.get('LikesGivenByAPI', 'N/A')}",
        reply_markup=join_keyboard()
    )

    if user_id != VIP_USER_ID:
        user_usage.setdefault(user_id, {})["like"] = 1
        like_usage[region] += 1

async def setup_webhook():
    """Setup webhook for production"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL', 'localhost')}/webhook/{API_TOKEN}"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")
    
    # Test webhook
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Webhook info: {webhook_info}")

def run_flask():
    """Run Flask app for webhook"""
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

async def main():
    """Main function to run the bot"""
    logger.info("Starting bot...")
    
    # Check if running on Render
    if os.environ.get('RENDER'):
        logger.info("Running on Render - Setting up webhook")
        await setup_webhook()
        
        # Start daily reset scheduler
        asyncio.create_task(daily_reset_scheduler())
        
        # Keep the event loop running
        while True:
            await asyncio.sleep(3600)
    else:
        # Local development - use polling
        logger.info("Running locally - Using polling")
        asyncio.create_task(daily_reset_scheduler())
        await dp.start_polling(bot)

if __name__ == "__main__":
    # Run Flask in separate thread for webhook
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
