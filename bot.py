import os
import asyncio
import logging
import urllib.parse
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://apki-website.netlify.app")

PORT = int(os.environ.get("PORT", 8080))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT SETUP ---
app = Client("LinkConverter", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER ---
routes = web.RouteTableDef()
@routes.get("/")
async def home(request): return web.Response(text="Link Converter Bot Running!")

# --- TERABOX BYPASS LOGIC (Basic API Example) ---
async def bypass_terabox(url):
    try:
        # Note: TeraBox links expire jaldi hain. 
        # Yahan hum ek Public API use kar rahe hain (Example ke liye)
        # Agar ye kaam na kare, to aapko apna 'TeraBox Downloader API' lagana hoga.
        
        # Example API: (Ye badal sakti hai)
        api_url = f"https://terabox-dl.com/api/get-link?url={url}" 
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                if 'direct_link' in data:
                    return data['direct_link']
    except:
        pass
    return None # Agar fail ho jaye

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 **Welcome to Link Converter!**\n\n"
        "Send me any **Direct Video Link** or **TeraBox Link**.\n"
        "I will convert it to a Stream Player Link for you."
    )

# --- LINK HANDLER ---
@app.on_message(filters.text & ~filters.command("start"))
async def convert_link(client, message):
    user_link = message.text.strip()
    
    # Check Valid Link
    if not user_link.startswith("http"):
        await message.reply_text("❌ Please send a valid link (starting with http/https).")
        return

    status_msg = await message.reply_text("🔄 **Processing Link...**")
    
    final_video_url = user_link
    file_name = "Video File"

    # 1. TERABOX DETECTION
    if "terabox" in user_link or "1024tera" in user_link:
        await status_msg.edit_text("🔍 **Extracting TeraBox Video...** (This may take time)")
        
        # Direct Link nikalne ki koshish
        # NOTE: TeraBox APIs aksar paid hoti hain ya band ho jati hain.
        # Agar aapke paas Direct Link hai, to bot best kaam karega.
        # Filhal hum maan lete hain user Direct Link dega ya hum bypass karenge.
        
        direct_link = await bypass_terabox(user_link)
        
        if direct_link:
            final_video_url = direct_link
            file_name = "TeraBox Video"
        else:
            # Agar bypass fail ho jaye, to user ko batayein
            await status_msg.edit_text(
                "⚠️ **TeraBox Bypass Failed.**\n"
                "Main abhi free API use kar raha hu jo shayad down hai.\n"
                "Please send a **Direct Video Link** (ending in .mp4/.mkv)."
            )
            return

    # 2. WEB APP LINK GENERATION
    safe_name = urllib.parse.quote(file_name)
    encoded_url = urllib.parse.quote(final_video_url) # URL ke andar URL hai, isliye encode zaruri hai
    
    # Final Magic Link
    web_player_link = f"{WEB_APP_URL}/?src={encoded_url}&name={safe_name}"

    await status_msg.edit_text(
        f"✅ **Link Converted!**\n\n"
        f"🔗 **Original:** {user_link[:30]}...\n"
        f"🚀 **Stream Link:**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch on My Player", url=web_player_link)]
        ])
    )

# --- RUNNER ---
async def start_services():
    app_runner = web.AppRunner(web.Application())
    app_runner.app.add_routes(routes)
    await app_runner.setup()
    site = web.TCPSite(app_runner, "0.0.0.0", PORT)
    await site.start()
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())