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
    return "Video Downloader Bot is Running Successfully!"

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

# Video Link handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # Check karna ki text me link hai ya nahi
    if "http://" not in url and "https://" not in url:
        bot.reply_to(message, "❌ Bhai, please ek valid video ka link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ Processing... API se video nikal raha hoon 🕵️‍♂️")

    try:
        # Cobalt API use karna (Best free API for downloading)
        api_url = "https://co.wuk.sh/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "vQuality": "720", # Video Quality
            "filenamePattern": "classic"
        }

        # API ko request bhejna
        bot.edit_message_text("🔄 Bypass kar raha hoon... wait karo ⚙️", chat_id=message.chat.id, message_id=msg.message_id)
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Agar API ne direct URL diya hai
            if 'url' in data:
                video_url = data['url']
                bot.edit_message_text("⬆️ Telegram par bhej raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
                
                # Direct URL se Telegram ko video bhejna (Fastest method)
                bot.send_video(
                    message.chat.id, 
                    video_url, 
                    caption="✅ **Video Downloaded!**\n🤖 Made with ❤️", 
                    reply_to_message_id=message.message_id,
                    parse_mode='Markdown'
                )
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Video nahi mila. Shayad link private hai.", chat_id=message.chat.id, message_id=msg.message_id)
        else:
            bot.edit_message_text(f"❌ API Server Error: {response.status_code}", chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Kuch gadbad ho gayi: {str(e)[:50]}...", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        # Flask aur Bot ko ek sath chalana
        t = Thread(target=run_server)
        t.start()
        print("Bot is running...")
        bot.infinity_polling()
