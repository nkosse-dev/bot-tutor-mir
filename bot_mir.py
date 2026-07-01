import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

# 1. CARGAR LAS CLAVES DESDE EL ARCHIVO LOCAL .ENV
load_dotenv()

# Corregido para que lea exactamente lo que pusimos en el .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. LA NUEVA PERSONALIDAD (Modo Test Interactivo)
INSTRUCCION_MAESTRA = (
    "Actúa como un profesor experto preparador del examen MIR de España. "
    "Sé conciso, profesional y básate en la evidencia más reciente. "
    "Si te envían una foto de un ECG o analítica, analízala con precisión clínica. "
    "REGLA DE ORO: Si el alumno te pide un caso clínico o una pregunta, preséntale el escenario clínico "
    "seguido de 4 opciones de respuesta (A, B, C, D). NUNCA des la solución correcta de inmediato. "
    "Debes esperar siempre a que el alumno te responda con su opción elegida. "
    "Cuando el alumno responda, dile si acertó o falló, explícale por qué la suya es correcta/incorrecta, "
    "y repasa brevemente por qué las otras opciones no lo eran."
    "REGLA DE FORMATO ESTRICTA: Escribe en texto plano y limpio. ESTÁ TOTALMENTE PROHIBIDO usar asteriscos (*) o formato Markdown. Para resaltar conceptos importantes utiliza letras MAYÚSCULAS, y para hacer listas utiliza un guion medio convencional (-)."
)

# 3. CONFIGURAR GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=INSTRUCCION_MAESTRA
)

# 4. CONFIGURAR TELEGRAM Y LA MEMORIA
bot = telebot.TeleBot(TELEGRAM_TOKEN)
sesiones_chat = {} # Aquí guardaremos la memoria de la conversación

# Función para obtener o crear la memoria del usuario
def obtener_chat(chat_id):
    if chat_id not in sesiones_chat:
        sesiones_chat[chat_id] = model.start_chat(history=[])
    return sesiones_chat[chat_id]

def enviar_respuesta_larga(chat_id, texto_completo):
    limite = 4000
    for i in range(0, len(texto_completo), limite):
        bot.send_message(chat_id, texto_completo[i:i+limite])

# === COMANDO: BORRAR MEMORIA ===
@bot.message_handler(commands=['reset', 'start'])
def reiniciar_memoria(message):
    chat_id = message.chat.id
    if chat_id in sesiones_chat:
        del sesiones_chat[chat_id]
    bot.reply_to(message, "🧠 Memoria borrada. Dime, ¿de qué especialidad quieres el siguiente test?")

# === MANEJADOR 1: TEXTO ===
@bot.message_handler(content_types=['text'])
def responder_texto(message):
    if message.text.startswith('/'): return
    try:
        bot.send_chat_action(message.chat.id, 'typing') 
        chat_memoria = obtener_chat(message.chat.id)
        respuesta = chat_memoria.send_message(message.text)
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Texto). Error: {str(e)}")

# === MANEJADOR 2: FOTOS ===
@bot.message_handler(content_types=['photo'])
def responder_foto(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        file_info = bot.get_file(message.photo[-1].file_id)
        foto_bytes = bot.download_file(file_info.file_path)
        imagen_data = {'mime_type': 'image/jpeg', 'data': foto_bytes}
        
        texto_usuario = message.caption if message.caption else "Analiza esta imagen."
        chat_memoria = obtener_chat(message.chat.id)
        respuesta = chat_memoria.send_message([texto_usuario, imagen_data])
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Foto). Error: {str(e)}")

# === MANEJADOR 3: VOZ ===
@bot.message_handler(content_types=['voice'])
def responder_voz(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        file_info = bot.get_file(message.voice.file_id)
        voz_bytes = bot.download_file(file_info.file_path)
        audio_data = {'mime_type': 'audio/ogg', 'data': voz_bytes}
        
        chat_memoria = obtener_chat(message.chat.id)
        respuesta = chat_memoria.send_message(["Transcribe y responde a este audio.", audio_data])
        enviar_respuesta_larga(message.chat.id, respuesta.text)
    except Exception as e:
        bot.reply_to(message, f"Fallo en Gemini (Audio). Error: {str(e)}")

# 5. EJECUCIÓN DIRECTA
if __name__ == '__main__':
    print("Bot Tutor MIR iniciado... Presiona Ctrl+C para detenerlo localmente.")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
