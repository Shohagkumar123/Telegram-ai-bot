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
    bot.reply_to(message, "হ্যালো! আমি আপনার এআই বট। আমাকে যেকোনো কিছু জিজ্ঞেস করতে পারেন।")

# কেউ অন্য মেসেজ দিলে
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # এখানে সবচেয়ে স্ট্যাবল (Stable) একটি ফ্রি মডেলের নাম দেওয়া হলো
        response = client.chat.completions.create(
            model="google/gemma-2-9b-it:free", 
            messages=[{"role": "user", "content": message.text}]
        )
        
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        # যদি কোনো সমস্যা হয়, বট আপনাকে জানাবে
        bot.reply_to(message, f"এআই এরর দিচ্ছে: {e}")

# Flask সার্ভার (Render এর জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Perfectly!"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
