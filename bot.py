import telebot
from openai import OpenAI
import os
from flask import Flask
import threading

# এনভায়রনমেন্ট ভেরিয়েবল থেকে API Key গুলো নেওয়া
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# টেলিগ্রাম এবং OpenRouter সেটআপ
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

# কেউ মেসেজ দিলে বট কী উত্তর দিবে তার ফাংশন
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # ইউজারকে দেখানো যে বট টাইপ করছে
        bot.send_chat_action(message.chat.id, 'typing')
        
        # OpenRouter এর ফ্রি মডেল দিয়ে উত্তর তৈরি করা (এখানে gemini-2.0-flash-lite এর ফ্রি ভার্সন ব্যবহার করা হয়েছে)
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free", 
            messages=[{"role": "user", "content": message.text}]
        )
        
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, "দুঃখিত, কোনো একটি সমস্যা হয়েছে! পরে আবার চেষ্টা করুন।")

# Render এ হোস্ট করার জন্য ছোট্ট একটি ফ্লাস্ক (Flask) ওয়েব সার্ভার
app = Flask(__name__)

@app.route('/')
def home():
    return "My Telegram AI Bot is Running!"

# বটকে ব্যাকগ্রাউন্ডে চালু রাখার ফাংশন
def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালু করা হচ্ছে
    threading.Thread(target=run_bot).start()
    # ওয়েব সার্ভার চালু করা হচ্ছে
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
