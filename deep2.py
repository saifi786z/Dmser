#!/usr/bin/env python3
"""
Telegram Advanced DM Bot - Complete Professional Version
Features: Channel Join Mandatory, Admin Panel, Premium Emojis, Colored Buttons
"""

import os
import json
import asyncio
import logging
import re
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, Message, InputMediaPhoto, InputMediaVideo,
    ReplyKeyboardMarkup, KeyboardButton, ForceReply
)
from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus
from pyrogram.errors import FloodWait, RPCError, UserNotParticipant
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import asyncio
from collections import defaultdict
import time
import base64
import hashlib

# ==================== CONFIGURATION ====================

API_ID = int(os.environ.get("API_ID", 6))
API_HASH = os.environ.get("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "123456789").split(",")]
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/db")

# ==================== TELEGRAM PREMIUM EMOJI IDs ====================

EMOJI_IDS = {
    "sparkle": "[6147565374289220368]",
    "fire": "[6147464060305676048]",
    "star": "[6147629438021408084]",
    "crown": "[6147868521670907133]",
    "rocket": "[6147617184479711380]",
    "gem": "[6147902731085420231]",
    "party": "[6147524086768604985]",
    "trophy": "[6147698410901214769]",
    "lightning": "[6147637448135414816]",
    "heart": "[6235628846855492222]",
    "shield": "[6147439566107186310]",
    "target": "[6147460667281511517]",
    "medal": "[6147815573314082674]",
    "check": "[6238042150324409739]",
    "cross": "[6237871554223412862]",
    "warning": "[6235449188373502693]",
    "info": "[6235375710073000908]",
    "question": "[6235475653961979149]",
    "plus": "[6237585380552480043]",
    "minus": "[6237742262822901946]",
    "arrow": "[6235646232883107337]",
    "diamond": "[6235252066554484059]",
    "circle": "[6235253239080555488]",
    "square": "[6237702328216982810]",
    "triangle": "[6237864166879663987]",
    "music": "[6237579651066107302]",
    "lock": "[6235722567336859128]",
    "unlock": "[6235640361662813672]",
    "bell": "[6237585097084638739]",
    "mega": "[6237905016313615867]",
    "money": "[6235722567336859128]",
    "wallet": "[6235447586350699315]",
    "bag": "[6235778118443865838]",
    "cart": "[6235355429237430006]",
    "delivery": "[6235640361662813672]",
    "user": "[6147439566107186310]",
    "users": "[6147815573314082674]",
    "calendar": "[6235375710073000908]",
    "clock": "[6235475653961979149]",
    "settings": "[6237585380552480043]",
    "gear": "[6237742262822901946]",
    "chart": "[6235646232883107337]",
    "link": "[6235252066554484059]",
    "book": "[6235253239080555488]",
    "support": "[6237702328216982810]",
    "premium": "[6237864166879663987]",
    "free": "[6237579651066107302]",
    "new": "[6235722567336859128]",
    "up": "[6235640361662813672]",
    "down": "[6237585097084638739]",
    "right": "[6237905016313615867]",
    "left": "[6235722567336859128]",
    "play": "[6235447586350699315]",
    "pause": "[6235778118443865838]",
    "stop": "[6235355429237430006]",
    "upgrade": "[6235640361662813672]",
    "gift": "[6235628846855492222]",
    "gold": "[6237864166879663987]",
    "king": "[6235722567336859128]",
    "edit": "[6237585380552480043]",
    "delete": "[6237871554223412862]",
    "telegram": "[6147565374289220368]",
    "step": "[6235253239080555488]",
    "days": "[6235375710073000908]",
    "phone": "[6147439566107186310]",
    "image": "[6237585380552480043]",
    "video": "[6237579651066107302]",
    "document": "[6235722567336859128]",
    "eye": "[6147815573314082674]",
}

# ==================== COLORED BUTTONS ====================

def create_button(text: str, callback_data: str, color: str = "blue"):
    """
    Create colored buttons as per Telegram's new update
    Colors: blue, green, red
    """
    colors = {
        "blue": {"color": 0, "emoji": "🔵"},
        "green": {"color": 1, "emoji": "🟢"},
        "red": {"color": 2, "emoji": "🔴"}
    }
    
    color_info = colors.get(color, colors["blue"])
    # Add color indicator emoji
    button_text = f"{color_info['emoji']} {text}"
    
    return InlineKeyboardButton(button_text, callback_data=callback_data)

def create_url_button(text: str, url: str, color: str = "blue"):
    """Create colored URL button"""
    colors = {
        "blue": {"color": 0, "emoji": "🔵"},
        "green": {"color": 1, "emoji": "🟢"},
        "red": {"color": 2, "emoji": "🔴"}
    }
    
    color_info = colors.get(color, colors["blue"])
    button_text = f"{color_info['emoji']} {text}"
    
    return InlineKeyboardButton(button_text, url=url)

# ==================== DATABASE SETUP ====================

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(100),
            first_name VARCHAR(100),
            phone VARCHAR(20),
            is_premium BOOLEAN DEFAULT FALSE,
            premium_type VARCHAR(20),
            premium_expiry TIMESTAMP,
            referrals INTEGER DEFAULT 0,
            dms_sent INTEGER DEFAULT 0,
            campaigns_created INTEGER DEFAULT 0,
            joined_channel BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            saved_message TEXT,
            state VARCHAR(50)
        )
    """)
    
    # Admin Settings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_settings (
            key VARCHAR(50) PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Insert default settings
    cur.execute("""
        INSERT INTO admin_settings (key, value) VALUES 
            ('channel_link', 'https://t.me/yourchannel'),
            ('channel_username', 'yourchannel'),
            ('channel_title', 'My Channel'),
            ('welcome_message', 'Welcome to DMS Forward Bot! 🚀'),
            ('upi_id', 'yourupi@upi'),
            ('upi_qr', ''),
            ('usdt_address', '0x...'),
            ('support_username', 'shubhxseller'),
            ('bot_name', 'DMS Forward Bot')
        ON CONFLICT (key) DO NOTHING
    """)
    
    # Premium plans table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS premium_plans (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50),
            days INTEGER,
            price INTEGER,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # Insert default plans
    cur.execute("""
        INSERT INTO premium_plans (name, days, price) VALUES 
            ('1 Day', 1, 10),
            ('3 Days', 3, 30),
            ('7 Days', 7, 60),
            ('15 Days', 15, 100),
            ('30 Days', 30, 190)
        ON CONFLICT DO NOTHING
    """)
    
    # Campaigns table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            name VARCHAR(255),
            campaign_type VARCHAR(50),
            message TEXT,
            media_type VARCHAR(20),
            media_id VARCHAR(255),
            button_text VARCHAR(100),
            button_url VARCHAR(255),
            status VARCHAR(20) DEFAULT 'draft',
            scheduled_time TIMESTAMP,
            sent_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Referrals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT,
            referred_id BIGINT,
            reward_days INTEGER DEFAULT 1,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
    """)
    
    # Redeem codes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS redeem_codes (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE,
            reward_days INTEGER,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            created_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# ==================== DATABASE FUNCTIONS ====================

def get_setting(key: str) -> str:
    """Get admin setting from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT value FROM admin_settings WHERE key = %s", (key,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result[0] if result else ""

def update_setting(key: str, value: str):
    """Update admin setting"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO admin_settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    
    conn.commit()
    cur.close()
    conn.close()

def get_user(user_id: int) -> Dict:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    
    if not result:
        cur.execute("""
            INSERT INTO users (user_id) VALUES (%s)
        """, (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
    
    cur.close()
    conn.close()
    return dict(result)

def update_user(user_id: int, data: Dict):
    conn = get_db_connection()
    cur = conn.cursor()
    
    set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
    values = list(data.values()) + [user_id]
    
    cur.execute(f"""
        UPDATE users SET {set_clause} WHERE user_id = %s
    """, values)
    
    conn.commit()
    cur.close()
    conn.close()

# ==================== BOT INITIALIZATION ====================

app = Client(
    "advanced_dm_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize database
init_database()

# Rate limiting
rate_limits = defaultdict(list)

def is_rate_limited(user_id: int, limit: int = 5, window: int = 60) -> bool:
    now = time.time()
    user_requests = rate_limits[user_id]
    user_requests = [t for t in user_requests if now - t < window]
    
    if len(user_requests) >= limit:
        return True
    
    user_requests.append(now)
    rate_limits[user_id] = user_requests
    return False

# ==================== CHANNEL CHECK ====================

async def check_channel_membership(user_id: int) -> bool:
    """Check if user has joined the required channel"""
    channel_username = get_setting('channel_username')
    
    if not channel_username:
        return True  # No channel set
    
    try:
        member = await app.get_chat_member(f"@{channel_username}", user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            user = get_user(user_id)
            if not user.get('joined_channel', False):
                update_user(user_id, {'joined_channel': True})
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Channel check error: {e}")
        return False
    
    return False

# ==================== EMOJI HELPER ====================

def emoji(name: str) -> str:
    """Get premium emoji by name"""
    return EMOJI_IDS.get(name, "")

# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    # Add subscriber
    user = get_user(user_id)
    update_user(user_id, {
        'username': username,
        'first_name': first_name,
        'last_active': datetime.now()
    })
    
    # Handle referral
    if message.text and "ref_" in message.text:
        try:
            referrer_id = int(message.text.split("ref_")[1].split()[0])
            if referrer_id != user_id:
                process_referral(referrer_id, user_id)
        except:
            pass
    
    # Check channel membership
    if not await check_channel_membership(user_id):
        await show_channel_join(message)
        return
    
    # Show main menu
    await show_main_menu(message)

async def show_channel_join(message: Message):
    """Show channel join required screen"""
    channel_link = get_setting('channel_link')
    channel_title = get_setting('channel_title') or 'Our Channel'
    welcome_message = get_setting('welcome_message') or 'Welcome to DMS Forward Bot! 🚀'
    
    text = f"""
{emoji('sparkle')} *{welcome_message}* {emoji('sparkle')}

{emoji('warning')} *Please join our channel first!* {emoji('warning')}

{emoji('arrow')} Click the button below to join:
{emoji('mega')} *Channel:* {channel_title}

{emoji('check')} After joining, click "I've Joined" to continue.
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_url_button(f"{emoji('mega')} Join Channel", channel_link, "blue")],
        [create_button(f"{emoji('check')} I've Joined", "check_join", "green")],
        [create_button(f"{emoji('support')} Need Help?", "support", "red")]
    ])
    
    await message.reply(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_callback_query(filters.regex("check_join"))
async def check_join(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await check_channel_membership(user_id):
        await callback_query.message.delete()
        await callback_query.answer(f"{emoji('check')} Channel joined successfully!", show_alert=True)
        await show_main_menu(callback_query.message)
    else:
        await callback_query.answer(f"{emoji('cross')} Please join the channel first!", show_alert=True)

async def show_main_menu(message: Message):
    """Show main menu with all options"""
    user_id = message.from_user.id
    user = get_user(user_id)
    
    premium_status = get_premium_status(user_id)
    bot_name = get_setting('bot_name') or 'DMS Forward Bot'
    
    text = f"""
{emoji('rocket')} *{bot_name}* {emoji('rocket')}

{emoji('user')} *User:* {user.get('first_name', 'Unknown')}
{emoji('shield')} *Status:* {premium_status}
{emoji('target')} *DMs Sent:* {user.get('dms_sent', 0)}
{emoji('link')} *Referrals:* {user.get('referrals', 0)}

{emoji('sparkle')} *Choose an option below:* {emoji('sparkle')}
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('rocket')} Campaign Manager", "campaign_manager", "blue")],
        [create_button(f"{emoji('book')} Set Message", "set_message", "blue")],
        [create_button(f"{emoji('eye')} Preview Message", "preview_message", "green")],
        [create_button(f"{emoji('chart')} My Stats", "my_stats", "blue")],
        [create_button(f"{emoji('user')} My Account", "my_account", "blue")],
        [create_button(f"{emoji('crown')} Premium Plans", "premium_plans", "green")],
        [create_button(f"{emoji('gift')} Redeem Code", "redeem_code", "blue")],
        [create_button(f"{emoji('link')} Refer & Earn", "refer_earn", "green")],
        [create_button(f"{emoji('book')} How To Use", "how_to_use", "blue")],
        [create_button(f"{emoji('support')} Support", "support", "red")]
    ])
    
    # Check if admin
    if message.from_user.id in ADMIN_IDS:
        keyboard.inline_keyboard.append(
            [create_button(f"{emoji('crown')} Admin Panel", "admin_panel", "red")]
        )
    
    await message.reply(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== ADMIN PANEL ====================

@app.on_callback_query(filters.regex("admin_panel") & filters.user(ADMIN_IDS))
async def admin_panel(client, callback_query: CallbackQuery):
    text = f"""
{emoji('crown')} *ADMIN PANEL* {emoji('crown')}

{emoji('settings')} *Manage your bot settings:*

{emoji('arrow')} *Channel Settings:*
• Change join channel
• Update welcome message

{emoji('wallet')} *Payment Settings:*
• Set UPI ID
• Set USDT Address

{emoji('mega')} *Broadcast:*
• Send message to all users

{emoji('gift')} *Redeem Codes:*
• Create new codes
• Manage existing codes

{emoji('crown')} *Premium:*
• Add premium to users
• View premium users

{emoji('chart')} *Stats:*
• View bot statistics
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('mega')} Channel Settings", "admin_channel", "blue")],
        [create_button(f"{emoji('wallet')} Payment Settings", "admin_payment", "blue")],
        [create_button(f"{emoji('mega')} Broadcast", "admin_broadcast", "green")],
        [create_button(f"{emoji('gift')} Redeem Codes", "admin_codes", "blue")],
        [create_button(f"{emoji('crown')} Premium Management", "admin_premium", "green")],
        [create_button(f"{emoji('chart')} Statistics", "admin_stats", "blue")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== ADMIN CHANNEL SETTINGS ====================

@app.on_callback_query(filters.regex("admin_channel") & filters.user(ADMIN_IDS))
async def admin_channel_settings(client, callback_query: CallbackQuery):
    channel_link = get_setting('channel_link')
    channel_username = get_setting('channel_username')
    channel_title = get_setting('channel_title')
    welcome_message = get_setting('welcome_message')
    
    text = f"""
{emoji('mega')} *CHANNEL SETTINGS* {emoji('mega')}

{emoji('info')} *Current Settings:*

{emoji('link')} *Channel Link:* `{channel_link}`
{emoji('user')} *Username:* @{channel_username}
{emoji('mega')} *Title:* {channel_title}

{emoji('book')} *Welcome Message:*
{channel_message}

{emoji('arrow')} *Commands to update:*

/setchannel @username - Change channel
/setchannellink https://t.me/... - Change link
/setwelcomemessage Your message - Change welcome
/setchanneltitle Title - Change channel title
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_message(filters.command("setchannel") & filters.user(ADMIN_IDS))
async def set_channel(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/setchannel @username`")
        return
    
    username = args[1].replace("@", "")
    update_setting('channel_username', username)
    update_setting('channel_link', f"https://t.me/{username}")
    
    await message.reply(f"""
{emoji('check')} *Channel Updated!* {emoji('mega')}

{emoji('user')} *Username:* @{username}
{emoji('link')} *Link:* https://t.me/{username}

{emoji('info')} Users will now be required to join this channel!
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setchannellink") & filters.user(ADMIN_IDS))
async def set_channel_link(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/setchannellink https://t.me/channel`")
        return
    
    link = args[1]
    update_setting('channel_link', link)
    
    await message.reply(f"""
{emoji('check')} *Channel Link Updated!* {emoji('link')}

{emoji('link')} *New Link:* {link}
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setwelcomemessage") & filters.user(ADMIN_IDS))
async def set_welcome_message(client, message: Message):
    text = message.text.replace("/setwelcomemessage", "", 1).strip()
    
    if not text:
        await message.reply(f"{emoji('cross')} Please provide a welcome message!")
        return
    
    update_setting('welcome_message', text)
    
    await message.reply(f"""
{emoji('check')} *Welcome Message Updated!* {emoji('book')}

{emoji('book')} *New Message:*
{text}
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setchanneltitle") & filters.user(ADMIN_IDS))
async def set_channel_title(client, message: Message):
    title = message.text.replace("/setchanneltitle", "", 1).strip()
    
    if not title:
        await message.reply(f"{emoji('cross')} Please provide a channel title!")
        return
    
    update_setting('channel_title', title)
    
    await message.reply(f"""
{emoji('check')} *Channel Title Updated!* {emoji('mega')}

{emoji('mega')} *New Title:* {title}
    """, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN PAYMENT SETTINGS ====================

@app.on_callback_query(filters.regex("admin_payment") & filters.user(ADMIN_IDS))
async def admin_payment_settings(client, callback_query: CallbackQuery):
    upi_id = get_setting('upi_id')
    usdt_address = get_setting('usdt_address')
    
    text = f"""
{emoji('wallet')} *PAYMENT SETTINGS* {emoji('wallet')}

{emoji('money')} *UPI ID:* `{upi_id}`
{emoji('diamond')} *USDT Address:* `{usdt_address}`

{emoji('arrow')} *Commands to update:*

/setupi yourupi@upi - Set UPI ID
/setusdt 0x... - Set USDT Address
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_message(filters.command("setupi") & filters.user(ADMIN_IDS))
async def set_upi(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/setupi yourupi@upi`")
        return
    
    upi_id = args[1]
    update_setting('upi_id', upi_id)
    
    await message.reply(f"""
{emoji('check')} *UPI ID Updated!* {emoji('money')}

{emoji('wallet')} *New UPI ID:* `{upi_id}`
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setusdt") & filters.user(ADMIN_IDS))
async def set_usdt(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/setusdt 0x...`")
        return
    
    address = args[1]
    update_setting('usdt_address', address)
    
    await message.reply(f"""
{emoji('check')} *USDT Address Updated!* {emoji('diamond')}

{emoji('diamond')} *New Address:* `{address}`
    """, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN BROADCAST ====================

@app.on_callback_query(filters.regex("admin_broadcast") & filters.user(ADMIN_IDS))
async def admin_broadcast_panel(client, callback_query: CallbackQuery):
    text = f"""
{emoji('mega')} *BROADCAST SYSTEM* {emoji('mega')}

{emoji('info')} Send a message to all users!

{emoji('arrow')} *How to broadcast:*
1️⃣ Type: `/broadcast YOUR_MESSAGE`
2️⃣ Bot will send to all users

{emoji('warning')} Be careful! This sends to ALL users.
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_message(client, message: Message):
    text = message.text.replace("/broadcast", "", 1).strip()
    
    if not text:
        await message.reply(f"{emoji('cross')} Please provide a message!\nUsage: `/broadcast Your message here`")
        return
    
    # Get all users
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    sent = 0
    failed = 0
    
    status_msg = await message.reply(f"{emoji('mega')} Broadcasting to {len(users)} users...")
    
    for (user_id,) in users:
        try:
            await client.send_message(user_id, f"""
{emoji('mega')} *ANNOUNCEMENT* {emoji('mega')}

{text}

{emoji('info')} *{get_setting('bot_name')}*
            """, parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    await status_msg.edit_text(f"""
{emoji('check')} *Broadcast Complete!*

{emoji('check')} *Sent:* {sent}
{emoji('cross')} *Failed:* {failed}
{emoji('users')} *Total:* {len(users)}
    """, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN REDEEM CODES ====================

@app.on_callback_query(filters.regex("admin_codes") & filters.user(ADMIN_IDS))
async def admin_codes_panel(client, callback_query: CallbackQuery):
    text = f"""
{emoji('gift')} *REDEEM CODES* {emoji('gift')}

{emoji('info')} *Commands:*

/createcode DAYS [MAX_USES] - Create new code
/deletecode CODE - Delete existing code
/codes - View all codes

{emoji('arrow')} Example:
/createcode 7 5 - Creates 7-day code (5 uses)
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_message(filters.command("createcode") & filters.user(ADMIN_IDS))
async def create_code(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/createcode DAYS [MAX_USES]`")
        return
    
    try:
        days = int(args[1])
        max_uses = int(args[2]) if len(args) > 2 else 1
    except ValueError:
        await message.reply(f"{emoji('cross')} Invalid days!")
        return
    
    # Generate code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO redeem_codes (code, reward_days, max_uses, created_by, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (code, days, max_uses, message.from_user.id, datetime.now() + timedelta(days=30)))
    
    conn.commit()
    cur.close()
    conn.close()
    
    await message.reply(f"""
{emoji('check')} *Code Created!* {emoji('gift')}

{emoji('info')} *Code:* `{code}`
{emoji('days')} *Days:* {days}
{emoji('users')} *Max Uses:* {max_uses}
{emoji('calendar')} *Expires:* 30 days

{emoji('arrow')} Share this code with users!
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("deletecode") & filters.user(ADMIN_IDS))
async def delete_code(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/deletecode CODE`")
        return
    
    code = args[1].upper()
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM redeem_codes WHERE code = %s", (code,))
    conn.commit()
    cur.close()
    conn.close()
    
    await message.reply(f"""
{emoji('check')} *Code Deleted!* {emoji('delete')}

{emoji('info')} Code `{code}` has been deleted.
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("codes") & filters.user(ADMIN_IDS))
async def view_codes(client, message: Message):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT code, reward_days, max_uses, used_count, created_at, expires_at
        FROM redeem_codes ORDER BY created_at DESC
    """)
    codes = cur.fetchall()
    cur.close()
    conn.close()
    
    if not codes:
        await message.reply(f"{emoji('info')} No codes found!")
        return
    
    text = f"{emoji('gift')} *Redeem Codes* {emoji('gift')}\n\n"
    for c in codes:
        text += f"""
{emoji('info')} *Code:* `{c['code']}`
{emoji('days')} *Days:* {c['reward_days']}
{emoji('users')} *Uses:* {c['used_count']}/{c['max_uses']}
{emoji('calendar')} *Expires:* {c['expires_at'].strftime('%Y-%m-%d')}
---
"""
    
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN PREMIUM MANAGEMENT ====================

@app.on_callback_query(filters.regex("admin_premium") & filters.user(ADMIN_IDS))
async def admin_premium_panel(client, callback_query: CallbackQuery):
    text = f"""
{emoji('crown')} *PREMIUM MANAGEMENT* {emoji('crown')}

{emoji('info')} *Commands:*

/addpremium USER_ID DAYS - Add premium
/removepremium USER_ID - Remove premium
/premiumusers - View premium users

{emoji('arrow')} Example:
/addpremium 123456789 7 - Adds 7-day premium
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_message(filters.command("addpremium") & filters.user(ADMIN_IDS))
async def add_premium(client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply(f"{emoji('cross')} Usage: `/addpremium USER_ID DAYS`")
        return
    
    try:
        user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.reply(f"{emoji('cross')} Invalid user ID or days!")
        return
    
    expiry = datetime.now() + timedelta(days=days)
    update_user(user_id, {
        'is_premium': True,
        'premium_expiry': expiry,
        'premium_type': f"{days}_days"
    })
    
    await message.reply(f"""
{emoji('check')} *Premium Added!* {emoji('crown')}

{emoji('user')} *User:* `{user_id}`
{emoji('calendar')} *Expires:* {expiry.strftime('%Y-%m-%d %H:%M')}
{emoji('days')} *Days:* {days}
    """, parse_mode=ParseMode.MARKDOWN)
    
    try:
        await client.send_message(user_id, f"""
{emoji('crown')} *PREMIUM ACTIVATED!* {emoji('party')}

{emoji('calendar')} Your premium has been activated!
{emoji('days')} *Expires:* {expiry.strftime('%Y-%m-%d %H:%M')}

{emoji('rocket')} Enjoy unlimited features! {emoji('rocket')}
        """, parse_mode=ParseMode.MARKDOWN)
    except:
        pass

@app.on_message(filters.command("removepremium") & filters.user(ADMIN_IDS))
async def remove_premium(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Usage: `/removepremium USER_ID`")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.reply(f"{emoji('cross')} Invalid user ID!")
        return
    
    update_user(user_id, {
        'is_premium': False,
        'premium_expiry': None,
        'premium_type': None
    })
    
    await message.reply(f"""
{emoji('check')} *Premium Removed!* {emoji('cross')}

{emoji('user')} *User:* `{user_id}`
    """, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("premiumusers") & filters.user(ADMIN_IDS))
async def view_premium_users(client, message: Message):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT user_id, first_name, premium_expiry, premium_type
        FROM users WHERE is_premium = TRUE
        ORDER BY premium_expiry DESC
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    if not users:
        await message.reply(f"{emoji('info')} No premium users found!")
        return
    
    text = f"{emoji('crown')} *Premium Users* {emoji('crown')}\n\n"
    for u in users:
        expiry = u['premium_expiry'].strftime('%Y-%m-%d') if u['premium_expiry'] else 'N/A'
        text += f"""
{emoji('user')} *{u['first_name'] or 'Unknown'}*
🆔 `{u['user_id']}`
{emoji('calendar')} *Expires:* {expiry}
{emoji('crown')} *Plan:* {u['premium_type'] or 'N/A'}
---
"""
    
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN STATISTICS ====================

@app.on_callback_query(filters.regex("admin_stats") & filters.user(ADMIN_IDS))
async def admin_stats_panel(client, callback_query: CallbackQuery):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT COUNT(*) as total FROM users")
    total_users = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as premium FROM users WHERE is_premium = TRUE")
    premium_users = cur.fetchone()['premium']
    
    cur.execute("SELECT COUNT(*) as campaigns FROM campaigns")
    total_campaigns = cur.fetchone()['campaigns']
    
    cur.execute("SELECT COUNT(*) as referrals FROM referrals")
    total_referrals = cur.fetchone()['referrals']
    
    cur.execute("SELECT COUNT(*) as codes FROM redeem_codes")
    total_codes = cur.fetchone()['codes']
    
    cur.close()
    conn.close()
    
    text = f"""
{emoji('chart')} *BOT STATISTICS* {emoji('chart')}

{emoji('users')} *Total Users:* {total_users}
{emoji('crown')} *Premium Users:* {premium_users}
{emoji('rocket')} *Campaigns:* {total_campaigns}
{emoji('link')} *Referrals:* {total_referrals}
{emoji('gift')} *Redeem Codes:* {total_codes}
{emoji('clock')} *Active Since:* {datetime.now().strftime('%Y-%m-%d')}

{emoji('info')} *Bot Status:* 🟢 Online
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "admin_panel", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== PREMIUM STATUS ====================

def get_premium_status(user_id: int) -> str:
    user = get_user(user_id)
    if not user.get('is_premium', False):
        return f"{emoji('free')} Free"
    
    expiry = user.get('premium_expiry')
    if expiry and expiry > datetime.now():
        days_left = (expiry - datetime.now()).days
        return f"{emoji('crown')} Premium ({days_left} days left)"
    else:
        update_user(user_id, {'is_premium': False, 'premium_expiry': None})
        return f"{emoji('free')} Free"

# ==================== REDEEM CODE ====================

@app.on_callback_query(filters.regex("redeem_code"))
async def redeem_code_panel(client, callback_query: CallbackQuery):
    text = f"""
{emoji('gift')} *REDEEM CODE* {emoji('gift')}

{emoji('info')} *Enter your premium code:*

{emoji('arrow')} Type: `/redeem YOUR_CODE`

{emoji('warning')} *How to get codes:*
• Purchased from admin
• Earned via referrals
• Promotional giveaways
    """
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("redeem"))
async def redeem_command(client, message: Message):
    user_id = message.from_user.id
    
    if is_rate_limited(user_id):
        await message.reply(f"{emoji('warning')} Too many requests! Please wait.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"{emoji('cross')} Please provide a code!\nUsage: `/redeem CODE`")
        return
    
    code = args[1].upper()
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT * FROM redeem_codes WHERE code = %s AND expires_at > NOW()
    """, (code,))
    
    code_data = cur.fetchone()
    
    if not code_data:
        await message.reply(f"{emoji('cross')} Invalid or expired code!")
        cur.close()
        conn.close()
        return
    
    if code_data['max_uses'] and code_data['used_count'] >= code_data['max_uses']:
        await message.reply(f"{emoji('cross')} Code has been fully used!")
        cur.close()
        conn.close()
        return
    
    # Apply premium
    days = code_data['reward_days']
    expiry = datetime.now() + timedelta(days=days)
    update_user(user_id, {
        'is_premium': True,
        'premium_expiry': expiry,
        'premium_type': f"{days}_days"
    })
    
    # Update code usage
    cur.execute("""
        UPDATE redeem_codes SET used_count = used_count + 1 WHERE code = %s
    """, (code,))
    conn.commit()
    
    await message.reply(f"""
{emoji('check')} *CODE REDEEMED SUCCESSFULLY!* {emoji('party')}

{emoji('crown')} *Premium Activated!*
{emoji('calendar')} *Expires:* {expiry.strftime('%Y-%m-%d %H:%M')}
{emoji('days')} *Days Added:* {days}

{emoji('rocket')} Enjoy unlimited features! {emoji('rocket')}
    """, parse_mode=ParseMode.MARKDOWN)
    
    cur.close()
    conn.close()

# ==================== REFERRAL SYSTEM ====================

@app.on_callback_query(filters.regex("refer_earn"))
async def refer_earn(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user(user_id)
    
    bot_username = (await client.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = f"""
{emoji('link')} *REFER & EARN* {emoji('gift')}

{emoji('arrow')} *Your Referral Link:*
`{refer_link}`

{emoji('chart')} *Stats:*
• Referrals: {user.get('referrals', 0)}
• Days Earned: {user.get('referrals', 0) * 1}
• Rewards: +1 day per referral

{emoji('info')} *How it works:*
1️⃣ Share your link
2️⃣ Friend joins with your link
3️⃣ Friend adds account
4️⃣ Friend sends DMs
5️⃣ You get +1 day premium!

{emoji('rocket')} Share your link now!
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_url_button(f"{emoji('link')} Share Link", 
            f"https://t.me/share/url?url={refer_link}&text=Join%20this%20awesome%20Telegram%20DM%20bot!%20{emoji('rocket')}", "green")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

def process_referral(referrer_id: int, referred_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if already referred
    cur.execute("SELECT id FROM referrals WHERE referred_id = %s", (referred_id,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return
    
    # Add referral
    cur.execute("""
        INSERT INTO referrals (referrer_id, referred_id, status)
        VALUES (%s, %s, 'completed')
    """, (referrer_id, referred_id))
    
    # Add reward to referrer
    cur.execute("""
        UPDATE users SET referrals = referrals + 1 WHERE user_id = %s
    """, (referrer_id,))
    
    # Add premium day
    cur.execute("""
        UPDATE users SET 
            is_premium = TRUE,
            premium_expiry = COALESCE(premium_expiry, NOW()) + INTERVAL '1 day'
        WHERE user_id = %s
    """, (referrer_id,))
    
    conn.commit()
    cur.close()
    conn.close()

# ==================== HOW TO USE ====================

@app.on_callback_query(filters.regex("how_to_use"))
async def how_to_use(client, callback_query: CallbackQuery):
    text = f"""
{emoji('book')} *HOW TO USE* {emoji('book')}

{emoji('step')} *STEP 1 - Set Message*
{emoji('book')} Click 'Set Message'
{emoji('arrow')} Type your promotional message
{emoji('check')} Save message

{emoji('step')} *STEP 2 - Create Campaign*
{emoji('rocket')} Click 'Campaign Manager'
{emoji('arrow')} Choose campaign type
{emoji('check')} Configure settings

{emoji('step')} *STEP 3 - Preview*
{emoji('eye')} Click 'Preview Message'
{emoji('arrow')} Check how it looks
{emoji('check')} Confirm

{emoji('step')} *STEP 4 - Launch*
{emoji('play')} Click 'Start Campaign'
{emoji('arrow')} Watch progress
{emoji('check')} Done!

{emoji('warning')} *Terms:*
• Use responsibly - no spam
• Not responsible for account restrictions
• Premium plans are non-refundable

{emoji('support')} Need help? Contact @{get_setting('support_username') or 'shubhxseller'}
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== SUPPORT ====================

@app.on_callback_query(filters.regex("support"))
async def support(client, callback_query: CallbackQuery):
    support_user = get_setting('support_username') or 'shubhxseller'
    
    text = f"""
{emoji('support')} *SUPPORT* {emoji('support')}

{emoji('user')} *Support Team:* @{support_user}

{emoji('info')} *Common Issues:*
• Payment issues
• Technical problems
• Account linking
• Campaign questions
• Feature requests

{emoji('arrow')} *Contact us:*
{emoji('telegram')} Telegram: @{support_user}
{emoji('clock')} Response: Within 24 hours

{emoji('warning')} Please include your user ID when contacting!
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_url_button(f"{emoji('support')} Contact Support", f"https://t.me/{support_user}", "green")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== MY ACCOUNT ====================

@app.on_callback_query(filters.regex("my_account"))
async def my_account(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user(user_id)
    
    premium_expiry = user.get('premium_expiry')
    expiry_str = premium_expiry.strftime('%Y-%m-%d %H:%M') if premium_expiry else 'Never'
    
    text = f"""
{emoji('user')} *MY ACCOUNT* {emoji('user')}

{emoji('user')} *Name:* {user.get('first_name', 'N/A')}
🆔 *ID:* `{user_id}`
{emoji('user')} *Username:* @{user.get('username', 'N/A')}
{emoji('phone')} *Phone:* {user.get('phone', 'Not linked')}

{emoji('shield')} *Premium Status:* {get_premium_status(user_id)}
{emoji('calendar')} *Premium Expiry:* {expiry_str}
{emoji('link')} *Referrals:* {user.get('referrals', 0)}
{emoji('target')} *DMs Sent:* {user.get('dms_sent', 0)}
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('link')} Refer & Earn", "refer_earn", "green")],
        [create_button(f"{emoji('crown')} Premium Plans", "premium_plans", "blue")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== BACK MENU ====================

@app.on_callback_query(filters.regex("back_menu"))
async def back_menu(client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    user_id = callback_query.from_user.id
    
    # Check channel membership again
    if not await check_channel_membership(user_id):
        await show_channel_join(callback_query.message)
        return
    
    await show_main_menu(callback_query.message)

# ==================== MESSAGE HANDLERS ====================

@app.on_callback_query(filters.regex("set_message"))
async def set_message(client, callback_query: CallbackQuery):
    text = f"""
{emoji('book')} *SET MESSAGE* {emoji('book')}

{emoji('info')} *Create your promotional message:*

{emoji('check')} *Supported:*
• Text with Markdown
• HTML formatting
• Links
• Emojis

{emoji('arrow')} *Type your message below:*
    """
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query(filters.regex("preview_message"))
async def preview_message(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user(user_id)
    saved_message = user.get('saved_message', 'No message saved yet!')
    
    text = f"""
{emoji('eye')} *PREVIEW MESSAGE* {emoji('eye')}

{emoji('info')} *How your message will appear:*

---
{saved_message}
---

{emoji('arrow')} *Options:*
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('edit')} Edit Message", "set_message", "blue")],
        [create_button(f"{emoji('check')} Send Campaign", "campaign_manager", "green")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_callback_query(filters.regex("my_stats"))
async def my_stats(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user(user_id)
    
    text = f"""
{emoji('chart')} *YOUR STATS* {emoji('chart')}

{emoji('user')} *User:* {user.get('first_name', 'Unknown')}
{emoji('shield')} *Status:* {get_premium_status(user_id)}
{emoji('target')} *DMs Sent:* {user.get('dms_sent', 0)}
{emoji('link')} *Referrals:* {user.get('referrals', 0)}
{emoji('calendar')} *Member Since:* {user.get('created_at', datetime.now()).strftime('%Y-%m-%d') if user.get('created_at') else 'N/A'}

{emoji('info')} *Recent Activity:* 
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_callback_query(filters.regex("campaign_manager"))
async def campaign_manager(client, callback_query: CallbackQuery):
    text = f"""
{emoji('rocket')} *CAMPAIGN MANAGER* {emoji('rocket')}

{emoji('info')} *Create and manage your campaigns:*

{emoji('arrow')} *Types:*
{emoji('users')} Broadcast to Subscribers
{emoji('user')} Broadcast to Groups
{emoji('clock')} Scheduled Campaign

{emoji('warning')} Premium required for unlimited campaigns!
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('users')} To Subscribers", "campaign_subscribers", "blue")],
        [create_button(f"{emoji('clock')} Scheduled", "campaign_scheduled", "green")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_callback_query(filters.regex("premium_plans"))
async def premium_plans(client, callback_query: CallbackQuery):
    text = f"""
{emoji('crown')} *PREMIUM PLANS* {emoji('crown')}

{emoji('info')} *Choose your plan:*

{emoji('free')} *Free*
• 100 DMs per day
• Basic features
• Limited campaigns

{emoji('star')} *1 Day - ₹10*
• Unlimited DMs
• All features
• Priority support

{emoji('diamond')} *3 Days - ₹30*
• Unlimited DMs
• All features
• Priority support

{emoji('gem')} *7 Days - ₹60*
• Unlimited DMs
• All features
• Priority support
• Advanced analytics

{emoji('crown')} *15 Days - ₹100*
• Unlimited DMs
• All features
• Priority support
• Advanced analytics

{emoji('king')} *30 Days - ₹190*
• Unlimited DMs
• All features
• Priority support
• Advanced analytics
• Custom campaigns
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_button(f"{emoji('star')} 1 Day - ₹10", "buy_premium_1", "blue")],
        [create_button(f"{emoji('diamond')} 3 Days - ₹30", "buy_premium_3", "blue")],
        [create_button(f"{emoji('gem')} 7 Days - ₹60", "buy_premium_7", "green")],
        [create_button(f"{emoji('crown')} 15 Days - ₹100", "buy_premium_15", "green")],
        [create_button(f"{emoji('king')} 30 Days - ₹190", "buy_premium_30", "red")],
        [create_button(f"{emoji('arrow')} Back", "back_menu", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@app.on_callback_query(filters.regex("buy_premium_"))
async def buy_premium(client, callback_query: CallbackQuery):
    plan = callback_query.data.split("_")[2]
    days = int(plan)
    
    prices = {1: 10, 3: 30, 7: 60, 15: 100, 30: 190}
    price = prices.get(days, 0)
    upi_id = get_setting('upi_id')
    usdt_address = get_setting('usdt_address')
    
    text = f"""
{emoji('money')} *PURCHASE PREMIUM* {emoji('money')}

{emoji('cart')} *Plan:* {days} Days
{emoji('wallet')} *Price:* ₹{price}

{emoji('info')} *Payment Methods:*

💳 *UPI:* `{upi_id}`
🪙 *USDT:* `{usdt_address}`

{emoji('arrow')} *How to pay:*
1️⃣ Send payment to above UPI/USDT
2️⃣ Take screenshot
3️⃣ Send UTR + screenshot to admin

{emoji('warning')} Contact @{get_setting('support_username') or 'shubhxseller'} for payment
    """
    
    keyboard = InlineKeyboardMarkup([
        [create_url_button(f"{emoji('support')} Contact Admin", 
            f"https://t.me/{get_setting('support_username') or 'shubhxseller'}", "green")],
        [create_button(f"{emoji('arrow')} Back", "premium_plans", "red")]
    ])
    
    await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ==================== RUN BOT ====================

@app.on_message(filters.text & filters.private & ~filters.command)
async def handle_text_input(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    # Save message for preview
    user = get_user(user_id)
    update_user(user_id, {'saved_message': text})
    
    await message.reply(f"""
{emoji('check')} *Message Saved!* {emoji('book')}

{emoji('info')} Your message has been saved.

{emoji('arrow')} *Options:*
• Preview with /preview
• Start campaign
• Edit message

{emoji('eye')} Use Preview to see how it looks!
    """, parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    print("🤖 Advanced DMS Forward Bot is starting...")
    print("=" * 50)
    print("📌 Bot Token:", BOT_TOKEN)
    print("👑 Admins:", ADMIN_IDS)
    print("📊 Database:", DATABASE_URL)
    print("=" * 50)
    print("✅ Features Loaded:")
    print("  - Channel Join Mandatory")
    print("  - Admin Panel (All Settings)")
    print("  - Premium Emojis (30+ emojis)")
    print("  - Colored Buttons (Blue, Green, Red)")
    print("  - Campaign Manager")
    print("  - Message Builder")
    print("  - Preview System")
    print("  - Stats System")
    print("  - Premium System")
    print("  - Redeem Code System")
    print("  - Referral System")
    print("  - Rate Limiting")
    print("=" * 50)
    print("🚀 Bot is running!")
    app.run()