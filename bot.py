import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
import aiosqlite
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = '7868878428:AAH44yu2ObIvTj4kGWHCibmoHqIiPFlMISM'          # ← আপনার বট টোকেন
ADMIN_ID = 6988762768                       # ← আপনার টেলিগ্রাম USER ID

# ৪টা চ্যানেল (নাম + লিংক আপডেট করুন)
CHANNELS = [
    {"name": "@channel1", "link": "https://t.me/codenexra"},
    {"name": "@channel2", "link": "https://t.me/tanvirtechhub"},
    {"name": "@channel3", "link": "https://t.me/cryptoalatr"},
    {"name": "@channel4", "link": "https://t.me/pixelhoster"},
]
# ============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_PATH = 'bot.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                join_status BOOLEAN DEFAULT FALSE,
                points INTEGER DEFAULT 0,
                referral_id TEXT,
                referred_by INTEGER,
                last_active DATE
            )
        ''')
        await db.commit()

async def check_subscription(user_id: int):
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch["name"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(text="Free Python Code", callback_data="free_code"),
         InlineKeyboardButton(text="Free Landing Page", callback_data="free_landing")],
        [InlineKeyboardButton(text="Custom Bot & Website", callback_data="custom"),
         InlineKeyboardButton(text="Referral", callback_data="referral")],
        [InlineKeyboardButton(text="Rules", callback_data="rules"),
         InlineKeyboardButton(text="Total Users", callback_data="total_users"),
         InlineKeyboardButton(text="Active Users Daily", callback_data="active_daily")],
        [InlineKeyboardButton(text="My Points", callback_data="my_points")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_join_keyboard():
    buttons = []
    for ch in CHANNELS:
        buttons.append([InlineKeyboardButton(text=f"Join {ch['name']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text="✅ সব চ্যানেল জয়েন হয়েছে", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, username, referral_id, last_active)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, f"ref_{user_id}", datetime.now().date().isoformat()))
        await db.commit()

    # Referral handling
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0].split('_')[1])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET referred_by = ? WHERE user_id = ? AND referred_by IS NULL", 
                               (referrer_id, user_id))
                await db.commit()
        except:
            pass

    subscribed = await check_subscription(user_id)
    
    if subscribed:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET join_status = TRUE, last_active = ? WHERE user_id = ?", 
                           (datetime.now().date().isoformat(), user_id))
            # Award point to referrer
            async with db.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,)) as cursor:
                ref = await cursor.fetchone()
                if ref and ref[0]:
                    await db.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (ref[0],))
            await db.commit()
        await message.answer("✅ সাবস্ক্রিপশন যাচাই হয়েছে! ফুল মেনু খুলছে।", reply_markup=get_main_menu())
    else:
        await message.answer(
            "🚫 **প্রথমে ৪টা চ্যানেলে জয়েন করুন**\n\n"
            "তারপর নিচের **✅ সব চ্যানেল জয়েন হয়েছে** বাটনে ক্লিক করুন।",
            reply_markup=get_join_keyboard()
        )

@dp.callback_query(F.data == "check_subscription")
async def check_after_join(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "✅ সব চ্যানেল জয়েন হয়েছে!\nমেইন মেনু খুলছে...",
            reply_markup=get_main_menu()
        )
    else:
        await callback.answer("এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)

# ================== অন্যান্য হ্যান্ডলার ==================
@dp.callback_query(F.data == "free_code")
async def free_code(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        await callback.answer("চ্যানেলে জয়েন করুন আগে!", show_alert=True)
        return
    keyboard = [[InlineKeyboardButton(text="✅ Ad দেখা শেষ", callback_data=f"ad_success_{user_id}")]]
    await callback.message.answer(
        "👀 Monetag Ad দেখুন:\nhttps://monetag.com/yourlink\n\nAd দেখা শেষ হলে Success বাটনে ক্লিক করুন।",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(F.data.startswith("ad_success_"))
async def ad_success(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    if callback.from_user.id != user_id:
        return
    await bot.send_message(ADMIN_ID, f"🔓 User {user_id} watched ad - wants free code.")
    await callback.answer("Admin কে নোটিফাই করা হয়েছে!", show_alert=True)

@dp.callback_query(F.data == "referral")
async def referral_handler(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(f"🔗 আপনার রেফারেল লিংক:\n`{ref_link}`", parse_mode="Markdown")

@dp.callback_query(F.data == "my_points")
async def my_points(callback: types.CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT points FROM users WHERE user_id = ?", (callback.from_user.id,)) as cursor:
            result = await cursor.fetchone()
            points = result[0] if result else 0
    await callback.answer(f"💰 আপনার পয়েন্ট: {points}", show_alert=True)

@dp.callback_query()
async def other_callbacks(callback: types.CallbackQuery):
    if callback.data == "rules":
        await callback.message.answer("📜 নিয়ম:\n• ৪টা চ্যানেল জয়েন করতে হবে\n• ১ রেফারেল = ১ পয়েন্ট")
    elif callback.data == "custom":
        await callback.message.answer("Custom Bot & Website এর জন্য Admin এর সাথে যোগাযোগ করুন।")
    elif callback.data == "total_users" and callback.from_user.id == ADMIN_ID:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as c:
                count = (await c.fetchone())[0]
        await callback.answer(f"Total Users: {count}", show_alert=True)
    elif callback.data == "active_daily" and callback.from_user.id == ADMIN_ID:
        today = datetime.now().date().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE last_active = ?", (today,)) as c:
                count = (await c.fetchone())[0]
        await callback.answer(f"Active Today: {count}", show_alert=True)

# Admin Commands
@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text[len('/broadcast '):].strip()
    if not text: 
        await message.answer("Usage: /broadcast Your message")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = [row[0] for row in await cursor.fetchall()]
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 {text}")
        except:
            pass
    await message.answer("Broadcast পাঠানো হয়েছে!")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())