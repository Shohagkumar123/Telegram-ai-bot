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

# ডিফল্ট একটি মডেল (এটি কাজ না করলেও সমস্যা নেই, আমরা টেলিগ্রাম থেকে পরিবর্তন করতে পারবো)
DEFAULT_MODEL = "google/gemini-1.5-flash:free"

# কোন ইউজার কোন মডেল ব্যবহার করছে, তা সেভ রাখার জন্য একটি ডিকশনারি
user_models = {}

# ১. কেউ /start লিখলে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "হ্যালো! আমি আপনার এআই বট।\n\n"
        "মডেল পরিবর্তন করতে চাইলে লিখুন:\n"
        "`/model মডেলের_নাম`\n\n"
        "যেমন: `/model meta-llama/llama-3-8b-instruct:free`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ২. মডেল পরিবর্তন করার কমান্ড (/model)
@bot.message_handler(commands=['model'])
def change_model(message):
    # ইউজার মেসেজ থেকে মডেলের নামটি আলাদা করা
    text_parts = message.text.split(maxsplit=1)
    
    if len(text_parts) > 1:
        new_model = text_parts[1].strip()
        user_models[message.chat.id] = new_model
        bot.reply_to(message, f"✅ সফলভাবে মডেল পরিবর্তন করা হয়েছে!\n\nনতুন মডেল: `{new_model}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ ভুল কমান্ড! সঠিক নিয়ম হলো:\n`/model <মডেলের_নাম>`\n\nউদাহরণ: `/model google/gemini-1.5-flash:free`", parse_mode='Markdown')

# ৩. কেউ অন্য মেসেজ দিলে AI যা উত্তর দিবে
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # ইউজারের সিলেক্ট করা মডেলটি নেওয়া (না থাকলে ডিফল্টটা নিবে)
        model_to_use = user_models.get(message.chat.id, DEFAULT_MODEL)
        
        response = client.chat.completions.create(
            model=model_to_use, 
            messages=[{"role": "user", "content": message.text}]
        )
        
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ এআই এরর দিচ্ছে: {e}")

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
