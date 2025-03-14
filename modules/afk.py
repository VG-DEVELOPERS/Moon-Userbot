import asyncio
import base64
import requests
from datetime import datetime

import humanize
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import ReplyCheck
from utils.db import db

# AFK Variables
AFK = False
AFK_REASON = ""
AFK_TIME = ""
USERS = {}
GROUPS = {}

# Autograb Variables
AUTO_GRAB = False

# Config
API_ID = int(db.get("core.config", "API_ID", 123456))
API_HASH = db.get("core.config", "API_HASH", "your_api_hash")
STRING_SESSION = db.get("core.config", "STRING_SESSION", "your_string_session")
BOT_USERNAME = db.get("core.config", "BOT_USERNAME", "@MudaeBot")  # Change if needed
API_URL = db.get("core.config", "API_URL", "http://cheatbot.twc1.net/getName")
API_TOKEN = db.get("core.config", "API_TOKEN", "TEST-API-TOKEN")

app = Client("MoonUserbot", session_string=STRING_SESSION, api_id=API_ID, api_hash=API_HASH)


def GetChatID(message: Message):
    """Get the group id of the incoming message"""
    return message.chat.id


def subtract_time(start, end):
    """Get humanized time"""
    subtracted = humanize.naturaltime(start - end)
    return str(subtracted)


# ✅ Command: Toggle Auto-Grab
@app.on_message(filters.command("autograb", prefix) & filters.me)
async def toggle_autograb(client: Client, message: Message):
    """Enable or disable autograb."""
    global AUTO_GRAB

    cmd = message.text.split()
    if len(cmd) < 2:
        return await message.reply("⚠️ Use `.autograb on` to enable or `.autograb off` to disable.")

    if cmd[1].lower() == "on":
        AUTO_GRAB = True
        await message.reply("✅ Auto-grab waifus is **enabled**!")
    elif cmd[1].lower() == "off":
        AUTO_GRAB = False
        await message.reply("❌ Auto-grab waifus is **disabled**!")
    else:
        await message.reply("⚠️ Invalid option! Use `.autograb on` or `.autograb off`.")


# ✅ Auto-Grab Waifu from Bot
@app.on_message(filters.chat(BOT_USERNAME) & filters.photo)
async def auto_grab_waifu(client: Client, message: Message):
    """Automatically grab waifus if enabled."""
    global AUTO_GRAB
    if not AUTO_GRAB:
        return  # Skip if auto-grab is disabled

    print("🔍 Checking waifu image...")

    # Download image
    file = await message.download(in_memory=True)
    encoded_string = base64.b64encode(bytes(file.getbuffer())).decode()

    # Send request to API
    data = {
        "api_token": API_TOKEN,
        "photo_b64": encoded_string
    }

    try:
        response = requests.post(API_URL, json=data)
        response_data = response.json()
        print("API Response:", response_data)  # Debugging

        if response_data.get("status") is True:
            char_name = response_data.get("name", "Unknown")
            print(f"✅ Character Matched: {char_name}")

            # Send the /grab command automatically
            await asyncio.sleep(1)
            await message.reply(f"/grab {char_name}")
            print(f"✅ Sent: /grab {char_name}")

        else:
            print("❌ No match found.")

    except Exception as e:
        print("⚠️ API Error:", e)


# ✅ Auto-Unset AFK
@app.on_message(filters.me, group=3)
async def auto_afk_unset(_, message: Message):
    global AFK, AFK_TIME, AFK_REASON, USERS, GROUPS

    if AFK:
        last_seen = subtract_time(datetime.now(), AFK_TIME).replace("ago", "").strip()
        reply = await message.reply(
            f"<code>While you were away (for {last_seen}), you received {sum(USERS.values()) + sum(GROUPS.values())} "
            f"messages from {len(USERS) + len(GROUPS)} chats</code>"
        )
        AFK = False
        AFK_TIME = ""
        AFK_REASON = ""
        USERS = {}
        GROUPS = {}
        await asyncio.sleep(5)
        await reply.delete()


# ✅ Help Menu
modules_help["autograb"] = {
    "autograb on/off": "Enable or disable auto waifu grabbing.",
  }
