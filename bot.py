import telebot
from openai import OpenAI
import os
from flask import Flask
import threading
import base64 # ছবিকে কোডে রূপান্তর করার জন্য নতুন লাইব্রেরি

# এনভায়রনমেন্ট ভেরিয়েবল
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

# ডিফল্ট মডেল (এটি গুগলের মডেল, যা টেক্সট এবং ছবি দুটোই দারুণ বোঝে)
DEFAULT_MODEL = "google/gemini-1.5-flash:free"
user_models = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "হ্যালো! আমি আপনার এআই বট।\n\n"
        "আমাকে যেকোনো প্রশ্ন করতে পারেন অথবা **যেকোনো ছবি পাঠিয়ে** জিজ্ঞেস করতে পারেন ছবিতে কী আছে!\n\n"
        "মডেল পরিবর্তন করতে চাইলে লিখুন:\n`/model মডেলের_নাম`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['model'])
def change_model(message):
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) > 1:
        new_model = text_parts[1].strip()
        user_models[message.chat.id] = new_model
        bot.reply_to(message, f"✅ মডেল পরিবর্তন করা হয়েছে!\n\nবর্তমান মডেল: `{new_model}`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ সঠিক নিয়ম:\n`/model google/gemini-1.5-flash:free`", parse_mode='Markdown')

# এখানে content_types এ 'photo' যুক্ত করা হয়েছে যেন বট ছবি নিতে পারে
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        model_to_use = user_models.get(message.chat.id, DEFAULT_MODEL)
        
        # যদি ইউজার শুধু টেক্সট পাঠায়
        if message.content_type == 'text':
            response = client.chat.completions.create(
                model=model_to_use, 
                messages=[{"role": "user", "content": message.text}]
            )
            
        # যদি ইউজার ছবি পাঠায়
        elif message.content_type == 'photo':
            # ১. টেলিগ্রাম থেকে ছবিটি ডাউনলোড করা
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # ২. ছবিকে Base64 কোডে রূপান্তর করা (এআইয়ের বোঝার জন্য)
            base64_image = base64.b64encode(downloaded_file).decode('utf-8')
            
            # ৩. ছবির সাথে কোনো ক্যাপশন আছে কিনা চেক করা
            user_text = message.caption if message.caption else "এই ছবিটিতে কী আছে বিস্তারিত বলুন।"
            
            # ৪. ছবি এবং টেক্সট একসাথে এআইকে পাঠানো
            vision_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
            
            response = client.chat.completions.create(
                model=model_to_use, 
                messages=[{"role": "user", "content": vision_content}]
            )
            
        # এআইয়ের উত্তর ইউজারকে পাঠানো
        reply_text = response.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ এআই এরর দিচ্ছে: {e}")

# Flask সার্ভার (Render এর জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running with Vision Capability!"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
