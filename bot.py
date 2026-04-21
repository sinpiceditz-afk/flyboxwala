import telebot
import requests
import os
from flask import Flask
from threading import Thread

# Token environment variable se lena
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Render server ke liye Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "All Video Downloader Bot is Active and Unstoppable!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to All-in-One Video Downloader!** 🚀\n\n"
        "🔗 Mujhe kisi bhi video ka Link bhejo aur main use direct yahan download karke dunga.\n\n"
        "**Supported:** YouTube, Instagram, Twitter, Pinterest, Facebook, TikTok, etc."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 🔥 Ye hain humare 5 Secret Servers (Agar ek fail hua toh dusra chalega)
COBALT_SERVERS = [
    "https://cobalt.q0.app/api/json",
    "https://api.cobalt.savetheweb.org/api/json",
    "https://api.drv.ovh/api/json",
    "https://cobalt.owo.vc/api/json",
    "https://dl.khub.app/api/json"
]

# Video Link handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # Check karna ki text me link hai ya nahi
    if "http://" not in url and "https://" not in url:
        bot.reply_to(message, "❌ Bhai, please ek valid video ka link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ Servers check kar raha hoon... wait 🕵️‍♂️")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url,
        "vQuality": "720", 
        "filenamePattern": "classic"
    }

    video_url = None

    # 🚀 API Rotator Logic (Sab servers ko ek-ek karke try karega)
    for i, server in enumerate(COBALT_SERVERS):
        try:
            bot.edit_message_text(f"🔄 Trying Server {i+1}... wait ⚙️", chat_id=message.chat.id, message_id=msg.message_id)
            
            # API ko request bhejna (10 second ka timeout)
            response = requests.post(server, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'url' in data:
                    video_url = data['url']
                    break  # Video mil gaya! Loop band karo
        except Exception:
            continue  # Agar server dead hai, toh agla try karo

    # Agar kisi ek server ne video dhundh liya
    if video_url:
        bot.edit_message_text("⬆️ Mil gaya! Telegram par bhej raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
        try:
            # Direct URL se Telegram ko video bhejna
            bot.send_video(
                message.chat.id, 
                video_url, 
                caption="✅ **Video Downloaded!**\n🤖 Made with ❤️", 
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as vid_err:
            # Agar video Telegram ki 50MB limit se bada nikla
            bot.edit_message_text(f"⚠️ **Video Telegram limit (50MB) se bada hai!**\n\n🔗 Aap is link se direct download kar sakte ho:\n{video_url}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.edit_message_text("❌ Saare servers busy hain ya link Private hai. Thodi der baad try karo.", chat_id=message.chat.id, message_id=msg.message_id)


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        # Flask aur Bot ko ek sath chalana
        t = Thread(target=run_server)
        t.start()
        print("Bot is running...")
        bot.infinity_polling()
