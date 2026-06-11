import os
import asyncio
import urllib.parse
from telethon import TelegramClient, events
from aiohttp import web

# Variables de entorno de Render
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

# Inicializar el cliente global como None
bot = None
# Usaremos un diccionario simple para que el bot recuerde el video en memoria RAM
cached_media = {}

async def stream_handler(request):
    global bot, cached_media
    file_id = int(request.match_info['file_id'])
    
    # Si el archivo no está en la memoria del bot, cerramos la conexión
    if file_id not in cached_media:
        return web.Response(text="Error: El archivo no existe o el bot se reinició.", status=404)
        
    headers = {
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes"
    }
    
    response = web.StreamResponse(status=200, headers=headers)
    await response.prepare(request)
    
    try:
        media_object = cached_media[file_id]
        # Transmitir el video en pequeños trozos en tiempo real directamente desde Telegram
        async for chunk in bot.iter_download(media_object, chunk_size=1024*1024):
            await response.write(chunk)
        return response
    except Exception as e:
        print(f"Error en streaming: {e}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def main():
    global bot
    
    # 1. Configurar y arrancar el servidor web de aiohttp primero
    server = web.Application()
    server.add_routes([web.get('/stream/{file_id}/{file_name}', stream_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"🌍 Servidor web iniciado en el puerto {PORT}")

    # 2. Inicializar el cliente de Telethon de forma segura
    bot = TelegramClient(None, API_ID, API_HASH)
    
    # Configurar los eventos del Bot
    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.reply("🚀 ¡Hola! Soy Blancid MTProto. Reenvíame el video gigante y te daré tu enlace directo sin límites.")

    @bot.on(events.NewMessage)
    async def handle_video(event):
        global cached_media
        if event.text and event.text.startswith('/'):
            return
            
        if event.message.video or event.message.document:
            msg = await event.reply("⚡ Procesando archivo gigante...")
            
            media = event.message.video or event.message.document
            file_id = event.message.id
            
            # Guardamos el objeto multimedia en la memoria RAM del bot
            cached_media[file_id] = media
            
            # Limpieza del nombre del archivo
            name = 'video.mp4'
            for attr in getattr(media, 'attributes', []):
                if hasattr(attr, 'file_name') and attr.file_name:
                    name = attr.file_name
                    break
                    
            safe_name = urllib.parse.quote(name)
            base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
            stream_link = f"{base_url}/stream/{file_id}/{safe_name}"
            
            await msg.edit(f"✅ ¡ENLACE DIRECTO REAL LISTO!:\n\n{stream_link}")

    # 3. Arrancar el bot con el Token definitivo
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 Bot Blancid MTProto iniciado correctamente.")
    
    # Mantener el script en ejecución continua
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
