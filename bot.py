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

# Definimos la variable global para usarla en el servidor web
bot = None

# Configuración del manejador de streaming para reproducir en la TV o PotPlayer
async def stream_handler(request):
    global bot
    
    # 1. Obtener la ID del chat y del mensaje desde la nueva URL estructurada
    chat_id = int(request.match_info['chat_id'])
    msg_id = int(request.match_info['file_id'])
    
    # Configurar las cabeceras para indicar que es un vídeo MP4 en streaming continuo
    headers = {
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes"
    }
    
    response = web.StreamResponse(status=200, headers=headers)
    await response.prepare(request)
    
    try:
        # 2. Buscamos el mensaje directamente usando el chat de origen real
        message = await bot.get_messages(chat_id, ids=msg_id)
        
        # 3. Transmitir el archivo de vídeo en fragmentos directamente al reproductor
        async for chunk in bot.iter_download(message.media, chunk_size=1024*1024):
            await response.write(chunk)
            
        return response
    except Exception as e:
        print(f"Error durante el envío de datos: {e}")
        return web.Response(text=f"Error en la retransmisión: {str(e)}", status=500)

async def main():
    global bot
    
    # 1. Configurar y arrancar el servidor web de aiohttp primero
    server = web.Application()
    # Cambiamos la ruta para que acepte la ID del chat antes de la ID del archivo
    server.add_routes([web.get('/stream/{chat_id}/{file_id}/{file_name}', stream_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"🌍 Servidor web iniciado en el puerto {PORT}")

    # 2. Inicializar el cliente de Telethon de forma segura DENTRO del bucle asíncrono
    bot = TelegramClient(None, API_ID, API_HASH)
    
    # Configurar los eventos del Bot
    @bot.on(events.NewMessage(pattern='/start'))
    async def start(event):
        await event.reply("🚀 ¡Hola! Soy Blancid MTProto. Reenvíame el video gigante y ahora SÍ te daré el link directo sin límites.")

    @bot.on(events.NewMessage)
    async def handle_video(event):
        if event.text and event.text.startswith('/'):
            return
            
        if event.message.video or event.message.document:
            msg = await event.reply("⚡ Saltando límites de Telegram... Procesando archivo gigante.")
            
            media = event.message.video or event.message.document
            
            # Extraemos la ID del chat origen y la ID del mensaje
            chat_id = event.chat_id
            file_id = event.message.id
            
            # Limpieza del nombre del archivo para evitar roturas de enlace
            name = 'video.mp4'
            for attr in getattr(media, 'attributes', []):
                if hasattr(attr, 'file_name') and attr.file_name:
                    name = attr.file_name
                    break
                    
            safe_name = urllib.parse.quote(name)
            base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
            
            # El nuevo formato de link incluye la ID del chat
            stream_link = f"{base_url}/stream/{chat_id}/{file_id}/{safe_name}"
            
            await msg.edit(f"✅ ¡ENLACE DIRECTO REAL LISTO!:\n\n{stream_link}")

    # 3. Arrancar el bot con el Token definitivo
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 Bot Blancid MTProto iniciado correctamente sin errores de hilo.")
    
    # Mantener el script en ejecución continua
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # Arrancar de forma segura el bucle principal de asyncio
    asyncio.run(main())
