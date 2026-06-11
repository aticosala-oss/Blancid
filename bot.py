import os
import asyncio
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web, ClientSession

TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy Blancid. Reenvíame cualquier video pesado y te daré el link directo para tu tele.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("❌ Por favor, reenvíame un video o archivo de video válido.")
        return

    msg = await update.message.reply_text("⏳ Procesando video gigante... Dame unos segundos.")
    
    file_id = video.file_id
    file_name = getattr(video, 'file_name', 'video.mp4') or 'video.mp4'
    
    # Limpiar espacios en blanco automáticamente
    safe_name = urllib.parse.quote(file_name)
    
    base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    stream_link = f"{base_url}/stream/{file_id}/{safe_name}"
    
    await msg.edit_text(f"✅ ¡Listo! Aquí tienes tu enlace directo para tu reproductor o SSIPTV:\n\n`{stream_link}`")

# ESTE ES EL MOTOR DE STREAMING REAL
async def stream_handler(request):
    file_id = request.match_info['file_id']
    bot = request.app['telegram_bot']
    
    try:
        # Obtener la ruta del archivo directo desde los servidores de Telegram
        tg_file = await bot.get_file(file_id)
        file_path = tg_file.file_path
        
        # Conectar el reproductor de tu casa con el archivo de Telegram en tiempo real
        async with ClientSession() as session:
            async with session.get(file_path) as response:
                headers = {
                    "Content-Type": response.headers.get("Content-Type", "video/mp4"),
                    "Content-Length": response.headers.get("Content-Length", "")
                }
                stream = web.StreamResponse(status=200, headers=headers)
                await stream.prepare(request)
                
                async for chunk in response.content.iter_any():
                    await stream.write(chunk)
                return stream
    except Exception as e:
        return web.Response(text=f"Error en streaming: {str(e)}", status=500)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_video))
    
    server = web.Application()
    server['telegram_bot'] = app.bot
    server.add_routes([web.get('/stream/{file_id}/{file_name}', stream_handler)])
    
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    
    await site.start()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
