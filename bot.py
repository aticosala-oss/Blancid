import os
import asyncio
from telethon import TelegramClient, events
from aiohttp import web

# Llaves del Servidor
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

# Iniciar el cliente nativo de Telegram
bot = TelegramClient('blancid_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("🚀 ¡Hola! Soy Blancid MTProto. Reenvíame el video gigante y ahora SÍ te daré el link directo sin límites.")

@bot.on(events.NewMessage)
async def handle_video(event):
    if event.text and event.text.startswith('/'):
        return
        
    # Verificar si el mensaje contiene un video o archivo pesado
    if event.message.video or event.message.document:
        msg = await event.reply("⚡ Saltando límites de Telegram... Procesando archivo gigante.")
        
        # Conseguir los datos del archivo
        media = event.message.video or event.message.document
        file_id = event.message.id  # Usamos la ID del mensaje para el enlace seguro
        
        # Crear nombre limpio sin espacios raros
        file_name = getattr(media, 'attributes', [None])[0]
        name = getattr(file_name, 'file_name', 'video.mp4') if file_name else 'video.mp4'
        safe_name = name.replace(" ", "%20")
        
        base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
        stream_link = f"{base_url}/stream/{file_id}/{safe_name}"
        
        await msg.edit(f"✅ ¡ENLACE DIRECTO REAL LISTO!:\n\n{stream_link}")

# MOTOR DE STREAMING DIRECTO PASO A PASO
async def stream_handler(request):
    msg_id = int(request.match_info['file_id'])
    
    # El bot leerá el video en pequeños trozos en tiempo real directamente desde Telegram
    headers = {"Content-Type": "video/mp4"}
    response = web.StreamResponse(status=200, headers=headers)
    await response.prepare(request)
    
    async for chunk in bot.iter_download(event.message, chunk_size=1024*1024):
        await response.write(chunk)
    return response

async def main():
    server = web.Application()
    server.add_routes([web.get('/stream/{file_id}/{file_name}', stream_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    await bot.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
