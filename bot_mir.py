import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

# 1. PEGA AQUÍ TUS CLAVES
TELEGRAM_TOKEN = "PEGA_TU_TOKEN_DE_TELEGRAM_AQUI"
GEMINI_API_KEY = "PEGA_TU_CLAVE_DE_GEMINI_AQUI"

# 2. CONFIGURAR GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. CONFIGURAR TELEGRAM
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
def responder_mensaje(message):
    try:
        # Esto hace que en Telegram ponga "Escribiendo..." mientras Gemini piensa
        bot.send_chat_action(message.chat.id, 'typing') 
        
        instruccion = "Actúa como un profesor experto en el examen MIR de España. Responde de forma estructurada a: "
        respuesta = model.generate_content(instruccion + message.text)
        bot.reply_to(message, respuesta.text)
    except Exception as e:
        bot.reply_to(message, "Ups, hubo un error de conexión con Gemini.")

# 4. EL TRUCO PARA RENDER (Servidor Web Falso)
app = Flask(__name__)

@app.route('/')
def home():
    return "El servidor del bot MIR está funcionando perfectamente."

def iniciar_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Arrancamos el bot en un proceso paralelo
    hilo_bot = threading.Thread(target=iniciar_bot)
    hilo_bot.start()
    
    # Arrancamos el servidor web que Render necesita
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto)
