import os
import asyncio
import logging
import aiohttp
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# StreamWish API Key (Yaha apni Key dalein ya Render Env me set karein)
STREAMWISH_API_KEY = os.environ.get("STREAMWISH_API_KEY", "")

# Render URL (Last me bina slash ke)
# Example: https://my-bot.onrender.com
MY_RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8080")

# Apki Website (Player)
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://apki-website.netlify.app")

PORT = int(os.environ.get("PORT", 8080))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT SETUP ---
app = Client("WishUploader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=10)

# --- STREAM SERVER (Bridge for StreamWish) ---
routes = web.RouteTableDef()

@routes.get("/")
async def home(request): return web.Response(text="StreamWish Uploader Running!")

@routes.get("/stream/{chat_id}/{message_id}")
async def stream_handler(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        message_id = int(request.match_info['message_id'])
        message = await app.get_messages(chat_id, message_id)
        media = message.video or message.document
        
        if not media: return web.Response(status=404)

        file_size = media.file_size
        file_name = getattr(media, "file_name", "video.mp4") or "video.mp4"
        
        range_header = request.headers.get("Range", 0)
        from_bytes, until_bytes = 0, file_size - 1
        if range_header:
            try:
                from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
                from_bytes = int(from_bytes)
                until_bytes = int(until_bytes) if until_bytes else file_size - 1
            except: pass
        
        length = until_bytes - from_bytes + 1
        headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(length),
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }

        response = web.StreamResponse(status=206 if range_header else 200, headers=headers)
        await response.prepare(request)

        async for chunk in app.download_media(message, offset=from_bytes, limit=length, in_memory=True, chunk_size=1024*1024):
            try: await response.write(chunk)
            except: break
            
        return response
    except: return web.Response(status=500)

# --- UPLOAD TO STREAMWISH LOGIC ---
async def upload_to_streamwish(direct_url, file_name):
    try:
        # StreamWish Remote Upload API
        api_url = f"https://api.streamwish.com/api/upload/url?key={STREAMWISH_API_KEY}&url={direct_url}&name={file_name}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                data = await resp.json()
                
                # Check agar upload start ho gaya
                if data.get('status') == 200 and data.get('result', {}).get('filecode'):
                    return data['result']['filecode']
                else:
                    logger.error(f"StreamWish Error: {data}")
                    return None
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **Hi!** Send me a video, I will upload it to StreamWish (Fast Server).")

@app.on_message(filters.private & (filters.video | filters.document))
async def handle_video(client, message):
    status_msg = await message.reply_text("🔄 **Processing...**\nCreating Bridge Link...")
    
    try:
        media = message.video or message.document
        fname = getattr(media, "file_name", f"Video_{message.id}.mp4") or "video.mp4"
        
        # 1. Create a Bridge Link (Render URL)
        # Ye link StreamWish use karega video khinchne ke liye
        bridge_link = f"{MY_RENDER_URL}/stream/{message.chat.id}/{message.id}"
        
        await status_msg.edit_text("☁️ **Sending to StreamWish Server...**\n(This might take a few seconds)")
        
        # 2. Upload to StreamWish
        file_code = await upload_to_streamwish(bridge_link, fname)
        
        if file_code:
            # 3. Generate Links
            watch_link = f"https://streamwish.com/{file_code}"
            embed_link = f"https://streamwish.com/e/{file_code}"
            
            # Web App Integration (Apni site par chalane ke liye)
            # Hum Embed link pass karenge
            safe_embed = urllib.parse.quote(embed_link)
            safe_name = urllib.parse.quote(fname)
            my_web_link = f"{WEB_APP_URL}/?src={safe_embed}&name={safe_name}&type=embed"

            await status_msg.edit_text(
                f"✅ **Upload Successful!**\n\n"
                f"📂 **File:** `{fname}`\n"
                f"🌍 **StreamWish Link:** {watch_link}\n\n"
                f"👇 **Watch on Your Player:**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ Play Fast (No Buffer)", url=my_web_link)]
                ])
            )
        else:
            await status_msg.edit_text("❌ **Upload Failed.**\nCheck API Key or File Size.")

    except Exception as e:
        logger.error(e)
        await status_msg.edit_text(f"❌ Error: {str(e)}")

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
