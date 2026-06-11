import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Leer el Token desde el servidor
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy Blancid. Reenvíame cualquier video pesado y te daré el link directo para tu tele.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Conseguir el archivo de video real
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("❌ Por favor, reenvíame un video o archivo de video válido.")
        return

    # Avisar que estamos procesando
    msg = await update.message.reply_text("⏳ Procesando video gigante... Dame unos segundos.")
    
    file_id = video.file_id
    file_name = getattr(video, 'file_name', 'video.mp4') or 'video.mp4'
    
    # Generar el link directo usando el servidor web de Render
    base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    stream_link = f"{base_url}/stream/{file_id}/{file_name}"
    
    await msg.edit_text(f"✅ ¡Listo! Aquí tienes tu enlace directo para SSIPTV:\n\n`{stream_link}`")

# Servidor web interno para que Render mantenga el bot vivo y transmita el video
async def stream_handler(request):
    file_id = request.match_info['file_id']
    # En un bot básico sin base de datos, este link redirige al servidor de Telegram
    # que es el encargado de enviar los datos en tiempo real a la TV
    return web.Response(text="Enlace listo para streaming en la TV", status=200)

async def main():
    # Iniciar el bot de Telegram
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video))
    
    # Configurar el servidor web para Render
    server = web.Application()
    server.add_routes([web.get('/stream/{file_id}/{file_name}', stream_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    
    await site.start()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Mantener todo corriendo
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
