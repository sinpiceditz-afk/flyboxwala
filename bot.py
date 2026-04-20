import telebot
import os
import yt_dlp
from flask import Flask
from threading import Thread

# Token environment variable se lenge
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Render ko zinda rakhne ke liye Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return "All-in-One Video Downloader Bot is Running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to All-in-One Video Downloader!** 🚀\n\n"
        "🔗 Mujhe kisi bhi video ka Link bhejo aur main use direct yahan download karke dunga.\n\n"
        "**Supported:** YouTube, Twitter, Pinterest, Facebook, Reddit, etc."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# Link aane par kya karna hai
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # Check karna ki message me link hai ya nahi
    if "http://" not in url and "https://" not in url:
        bot.reply_to(message, "❌ Bhai, please ek valid video ka link bhejo.")
        return

    msg = bot.reply_to(message, "⏳ Video dhoondh raha hoon... thoda wait karo 🕵️‍♂️")
    file_name = None

    try:
        # yt-dlp ki settings (Maximum 50MB ki file allow karega kyunki Telegram ki limit hai)
        ydl_opts = {
            'outtmpl': f'video_{message.message_id}.%(ext)s',
            'format': 'best[ext=mp4]/best', # MP4 format try karega
            'max_filesize': 50000000, # 50 MB limit
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("⬇️ Downloading start ho gayi hai... 🚀", chat_id=message.chat.id, message_id=msg.message_id)
            
            # Video extract aur download karna
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Video upload karna
        bot.edit_message_text("⬆️ Telegram par upload kar raha hoon... 🌐", chat_id=message.chat.id, message_id=msg.message_id)
        
        with open(file_name, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption="✅ **Video Downloaded Successfully!**\n🤖 Made with ❤️", 
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
        
        # Success ke baad purana "uploading" wala message delete kar dena
        bot.delete_message(message.chat.id, msg.message_id)

    except yt_dlp.utils.DownloadError as e:
        bot.edit_message_text(f"❌ **Download Failed!**\nHo sakta hai link private ho ya video 50MB se badi ho.\n\nError: {str(e)[:100]}...", chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Server Error: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)
    
    finally:
        # Downloaded file ko delete karna taaki server ki memory full na ho
        if file_name and os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
    else:
        # Background me server chalana
        t = Thread(target=run_server)
        t.start()
        
        # Bot start karna
        print("Bot is running...")
        bot.infinity_polling()
