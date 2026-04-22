import telebot
import requests
import os
import urllib.parse
import re
from flask import Flask
from threading import Thread

# Token environment variable se lena
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Render server ke liye Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running smoothly!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 **Welcome to the Ultimate Downloader!** 🚀\n\n🔗 Koi bhi video ka Link bhejo (YT, Insta, FB, Pinterest) aur magic dekho!")

# 🔥 AI URL Cleaner & Encoder (Isi ki wajah se error aa raha tha)
def clean_and_encode_url(url):
    # Tracking IDs (jaise ?si= ya ?igsh=) ko remove karna taaki API confuse na ho
    url = re.sub(r'(\?|&)(si|igsh|utm_[a-z]+)=[^&]+', '', url)
    url = url.rstrip('?&')
    
    # URL ko encode karna (Safe mode)
    encoded_url = urllib.parse.quote(url, safe='')
    return encoded_url, url

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    
    if "http://" not in text and "https://" not in text:
        bot.reply_to(message, "❌ Bhai, please ek valid video ka link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ Link ko clean aur analyze kar raha hoon... 🕵️‍♂️")

    # Link ko saaf karna
    encoded_url, clean_url = clean_and_encode_url(text)
    video_url = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    try:
        bot.edit_message_text("🔄 API 1 (Premium Server) Try kar raha hoon... ⚙️", chat_id=message.chat.id, message_id=msg.message_id)
        
        # 🚀 API 1: Ryzendesu (Best for YouTube & Insta)
        res1 = requests.get(f"https://api.ryzendesu.vip/api/downloader/vdl?url={encoded_url}", headers=headers, timeout=15).json()
        
        # Data me se video link nikalna
        if isinstance(res1, dict):
            if "url" in res1 and str(res1["url"]).startswith("http"):
                video_url = res1["url"]
            elif "data" in res1 and isinstance(res1["data"], dict) and "url" in res1["data"]:
                video_url = res1["data"]["url"]
            elif "data" in res1 and isinstance(res1["data"], list) and len(res1["data"]) > 0:
                for item in res1["data"]:
                    if isinstance(item, dict) and (item.get("type") == "video" or item.get("extension") == "mp4"):
                        video_url = item.get("url") or item.get("dl")
                        break
                if not video_url and "url" in res1["data"][0]:
                    video_url = res1["data"][0]["url"]

        # 🚀 API 2: Siputzx (Agar API 1 fail ho jaye)
        if not video_url:
            bot.edit_message_text("🔄 API 2 Try kar raha hoon... ⚙️", chat_id=message.chat.id, message_id=msg.message_id)
            
            # Link ke hisaab se API select karna
            if "youtube.com" in clean_url or "youtu.be" in clean_url:
                api_url = f"https://api.siputzx.my.id/api/d/ytmp4?url={encoded_url}"
            elif "instagram.com" in clean_url:
                api_url = f"https://api.siputzx.my.id/api/d/igdl?url={encoded_url}"
            else:
                api_url = f"https://api.siputzx.my.id/api/d/allinone?url={encoded_url}"
            
            res2 = requests.get(api_url, headers=headers, timeout=15).json()
            if res2.get("status"):
                data = res2.get("data")
                if isinstance(data, dict):
                    video_url = data.get("dl") or data.get("url")
                elif isinstance(data, list) and len(data) > 0:
                    video_url = data[0].get("url") or data[0].get("dl")

    except Exception as e:
        print("API Error: ", e)
        pass

    # Agar Video URL mil gaya toh bhej do
    if video_url:
        bot.edit_message_text("⬆️ Mil gaya! Telegram par upload kar raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
        try:
            bot.send_video(
                message.chat.id, 
                video_url, 
                caption=f"✅ **Video Downloaded!**\n🤖 Made with ❤️", 
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"⚠️ **Video Telegram ki limit (50MB) se bada hai!**\n\n🔗 Aap is link se direct download kar sakte ho:\n{video_url}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.edit_message_text("❌ Download Failed. Ya toh link private hai, ya server busy hai.", chat_id=message.chat.id, message_id=msg.message_id)


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        t = Thread(target=run_server)
        t.start()
        print("Bot is running...")
        bot.infinity_polling()
