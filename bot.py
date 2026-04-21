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
    return "God Mode Video Downloader Bot is Running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to the Ultimate Video Downloader!** 🚀\n\n"
        "🔗 Mujhe kisi bhi video ka Link bhejo (YT, Insta, FB, Pinterest, TikTok) aur magic dekho!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 🔥 Smart Data Extractor (API se video link dhoondhne ka logic)
def find_video_url(data):
    if isinstance(data, dict):
        # Pehle check karo agar koi direct 'video', 'url', ya 'hd' key hai
        for key in ['video', 'url', 'hd', 'sd', 'link', 'medias']:
            if key in data and isinstance(data[key], str) and data[key].startswith('http'):
                return data[key]
        # Warna deep search karo
        for key, value in data.items():
            res = find_video_url(value)
            if res: return res
    elif isinstance(data, list):
        for item in data:
            res = find_video_url(item)
            if res: return res
    elif isinstance(data, str) and data.startswith('http') and ('mp4' in data or 'video' in data):
        return data
    return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    if "http://" not in url and "https://" not in url:
        bot.reply_to(message, "❌ Bhai, please ek valid video ka link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ API se video extract kar raha hoon... wait 🕵️‍♂️")

    # 🔥 Top 3 Developer APIs (Ye Render ko block nahi karte)
    APIS = [
        f"https://api.joshweb.click/api/alldl?url={url}",
        f"https://api.siputzx.my.id/api/d/allinone?url={url}",
        f"https://api.agatz.xyz/api/alldownloader?url={url}"
    ]

    video_url = None

    for i, api_link in enumerate(APIS):
        try:
            bot.edit_message_text(f"🔄 Trying Server {i+1}... ⚙️", chat_id=message.chat.id, message_id=msg.message_id)
            
            response = requests.get(api_link, timeout=15)
            if response.status_code == 200:
                data = response.json()
                extracted_link = find_video_url(data)
                
                if extracted_link and extracted_link.startswith("http"):
                    video_url = extracted_link
                    break # Link mil gaya, loop band karo
        except Exception:
            continue

    if video_url:
        bot.edit_message_text("⬆️ Mil gaya! Telegram par upload kar raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
        try:
            bot.send_video(
                message.chat.id, 
                video_url, 
                caption="✅ **Downloaded Successfully!**\n🤖 Made with ❤️", 
                reply_to_message_id=message.message_id
            )
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"⚠️ **Video Telegram ki limit (50MB) se bada hai!**\n\n🔗 Direct Download Link:\n{video_url}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.edit_message_text("❌ Download Failed. Ya toh link private hai, ya servers change ho gaye hain.", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        t = Thread(target=run_server)
        t.start()
        print("Bot is running...")
        bot.infinity_polling()
