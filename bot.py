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
    return "All Video Downloader Bot is Active!"

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

    msg = bot.reply_to(message, "⏳ Processing... Naye API server se video nikal raha hoon 🕵️‍♂️")

    try:
        # Cobalt ki Official aur New API
        api_url = "https://api.cobalt.tools/api/json"
        
        # Ye headers bohot zaruri hain, iske bina API block kar degi
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://cobalt.tools",
            "Referer": "https://cobalt.tools/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
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
            
            # Agar API ne direct URL diya hai (status: stream ya redirect aata hai)
            if data.get('status') in ['redirect', 'stream', 'success'] and 'url' in data:
                video_url = data['url']
                bot.edit_message_text("⬆️ Telegram par bhej raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
                
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
                    # Agar video 50MB se bada hua ya Telegram upload fail hua toh direct link de dega
                    bot.edit_message_text(f"⚠️ **Video size bada hai ya upload fail hua!**\n\n🔗 Aap is link se direct download kar sakte ho:\n{video_url}", chat_id=message.chat.id, message_id=msg.message_id)
            else:
                error_msg = data.get('text', 'Link private hai ya support nahi karta.')
                bot.edit_message_text(f"❌ Video nahi mila: {error_msg}", chat_id=message.chat.id, message_id=msg.message_id)
        else:
            bot.edit_message_text(f"❌ API Server Error: Code {response.status_code}. Server abhi busy hai.", chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Kuch gadbad ho gayi: {str(e)[:100]}...", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        # Flask aur Bot ko ek sath chalana
        t = Thread(target=run_server)
        t.start()
        print("Bot is running...")
        bot.infinity_polling()
