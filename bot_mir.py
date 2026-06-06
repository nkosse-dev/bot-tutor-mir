import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

# 1. LEER LAS CLAVES DESDE RENDER (MÉTODO SEGURO)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. CONFIGURAR GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. CONFIGURAR TELEGRAM
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
@bot.message_handler(func=lambda message: True)
def responder_mensaje(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing') 
        instruccion = "Actúa como un profesor experto en el examen MIR de España. Responde de forma estructurada a: "
        respuesta = model.generate_content(instruccion + message.text)
        bot.reply_to(message, respuesta.text)
    except Exception as e:
        # ¡AHORA VEREMOS EL ERROR REAL!
        error_real = str(e)
        bot.reply_to(message, f"Fallo en Gemini. El error técnico es: {error_real}")
# 4. EL TRUCO PARA RENDER (Servidor Web Falso)
app = Flask(__name__)

@app.route('/')
def home():
    return "El servidor del bot MIR está funcionando perfectamente."

def iniciar_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    hilo_bot = threading.Thread(target=iniciar_bot)
    hilo_bot.start()
    
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto)
