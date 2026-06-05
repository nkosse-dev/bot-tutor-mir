import telebot
import google.generativeai as genai

# 1. PEGA AQUÍ TUS CLAVES
TELEGRAM_TOKEN = "PEGA_TU_TOKEN_DE_TELEGRAM_AQUI"
GEMINI_API_KEY = "PEGA_TU_CLAVE_DE_GEMINI_AQUI"

# 2. CONFIGURAR GEMINI
genai.configure(api_key=GEMINI_API_KEY)
# Usamos Gemini 1.5 Flash por su rapidez y eficacia
model = genai.GenerativeModel('gemini-1.5-flash') 

# 3. CONFIGURAR TELEGRAM
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 4. LA LÓGICA DEL BOT (Qué hace cuando le escribes)
@bot.message_handler(func=lambda message: True)
def responder_mensaje(message):
    try:
        # Aquí le damos la "personalidad" de tutor MIR
        instruccion_sistema = "Actúa como un profesor experto en el examen MIR de España. Responde de forma estructurada a la siguiente consulta del alumno: "
        consulta_completa = instruccion_sistema + message.text
        
        # Enviamos a Gemini
        respuesta_gemini = model.generate_content(consulta_completa)
        
        # Devolvemos la respuesta a Telegram
        bot.reply_to(message, respuesta_gemini.text)
        
    except Exception as e:
        bot.reply_to(message, "Ups, hubo un error de conexión con Gemini.")

# Esto mantiene al bot escuchando sin parar
print("Bot iniciado y esperando mensajes...")
bot.polling(none_stop=True)