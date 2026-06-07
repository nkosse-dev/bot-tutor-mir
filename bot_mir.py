import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

# 1. LEER LAS CLAVES DESDE RENDER (MÉTODO SEGURO)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. CONFIGURAR GEMINI (Usando la versión actualizada 2.5)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. CONFIGURAR TELEGRAM
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Función auxiliar para cortar y enviar respuestas muy largas sin bloquear Telegram
def enviar_respuesta_larga(chat_id, texto_completo):
    limite = 4000
    for i in range(0, len(texto_completo), limite):
        bot.send_message(chat_id, texto_completo[i:i+limite])

# Instrucción base para entrenar a la IA en cada interacción
INSTRUCCION_MAESTRA = "Actúa como un profesor experto en el examen MIR de España. Responde de forma muy estructurada, docente y precisa a la siguiente consulta del alumno: "


# === MANEJADOR 1: PARA MENSAJES DE TEXTO ===
@bot.message_handler(func=lambda message: True)
def responder_texto(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing') 
        respuesta = model.generate_content(INSTRUCCION_MAESTRA + message.text)
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Texto). Error técnico: {str(e)}")


# === MANEJADOR 2: PARA FOTOS (ECGs, Radiografías, Dermatología...) ===
@bot.message_handler(content_types=['photo'])
def responder_foto(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Descargamos la foto enviada con la resolución más alta
        file_info = bot.get_file(message.photo[-1].file_id)
        foto_bytes = bot.download_file(file_info.file_path)
        
        # Preparamos la estructura de la imagen para Gemini
        imagen_data = {
            'mime_type': 'image/jpeg',
            'data': foto_bytes
        }
        
        # Si el usuario escribió un texto junto a la foto, se lo pasamos. Si no, le pedimos un análisis general
        texto_usuario = message.caption if message.caption else "Analiza esta imagen médica orientada a una pregunta del examen MIR."
        
        respuesta = model.generate_content([INSTRUCCION_MAESTRA + texto_usuario, imagen_data])
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Foto). Error técnico: {str(e)}")


# === MANEJADOR 3: PARA NOTAS DE VOZ (Dictar casos clínicos) ===
@bot.message_handler(content_types=['voice'])
def responder_voz(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Descargamos la nota de voz (.ogg) directamente desde Telegram
        file_info = bot.get_file(message.voice.file_id)
        voz_bytes = bot.download_file(file_info.file_path)
        
        # Preparamos la estructura del audio para Gemini
        audio_data = {
            'mime_type': 'audio/ogg',
            'data': voz_bytes
        }
        
        # Le indicamos que escuche el audio y lo procese bajo el rol del MIR
        respuesta = model.generate_content([INSTRUCCION_MAESTRA + "Escucha atentamente este audio clínico y responde a lo que se solicita.", audio_data])
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Audio). Error técnico: {str(e)}")


# 4. EL TRUCO PARA RENDER (Servidor Web Falso)
app = Flask(__name__)

@app.route('/')
def home():
    return "El servidor del bot MIR multimodal está activo y funcionando."

def iniciar_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    hilo_bot = threading.Thread(target=iniciar_bot)
    hilo_bot.start()
    
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto)
