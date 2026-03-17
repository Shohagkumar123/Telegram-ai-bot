import telebot
from openai import OpenAI
import os
from flask import Flask
import threading

# এনভায়রনমেন্ট ভেরিয়েবল
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

# কেউ /start লিখলে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("✅ /start কমান্ড এসেছে!", flush=True) 
    bot.reply_to(message, "হ্যালো! আমি রেডি। আমাকে কিছু জিজ্ঞেস করুন।")

# কেউ অন্য মেসেজ দিলে
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(f"📩 ইউজার মেসেজ দিয়েছে: {message.text}", flush=True) 
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free", 
            messages=[{"role": "user", "content": message.text}]
        )
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        print("✅ AI উত্তর দিয়েছে!", flush=True)
        
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        bot.reply_to(message, "দুঃখিত, এআই এখন উত্তর দিতে পারছে না।")

# Flask সার্ভার
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

# বটকে চালু রাখার ফাংশন (এররটি এখানেই ঠিক করা হয়েছে)
def run_bot():
    print("🤖 Bot Polling Started...", flush=True)
    # non_stop=True সরিয়ে দেওয়া হয়েছে
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
