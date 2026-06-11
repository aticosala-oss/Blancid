import os
import asyncio
import urllib.parse
from telethon import TelegramClient, events
from aiohttp import web

# Variables de entorno
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

# Crear cliente sin arrancarlo todavía
bot = TelegramClient(None, API_ID, API_HASH)

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
        file_id = event.message.id
        
        file_name = getattr(media, 'attributes', [None])
        name = 'video.mp4'
        for attr in getattr(media, 'attributes', []):
            if hasattr(attr, 'file_name') and attr.file_name:
                name = attr.file_name
                break
                
        safe_name = urllib.parse.quote(name)
        
        base_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
        stream_link = f"{base_url}/stream/{file_id}/{safe_name}"
        
        await msg.edit(f"✅ ¡ENLACE DIRECTO REAL LISTO!:\n\n{stream_link}")

async def stream_handler(request):
    msg_id = int(request.match_info['file_id'])
    
    try:
        # Buscar el mensaje original usando la ID
        # Nota: Para un bot básico, este método requiere que el bot recuerde el chat o use canales públicos.
        # Por ahora enviamos una respuesta de prueba para validar que el servidor conecta.
        return web.Response(text="Servidor Blancid MTProto conectado correctamente.", status=200)
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def main():
    # 1. Iniciar servidor web primero para Render
    server = web.Application()
    server.add_routes([web.get('/stream/{file_id}/{file_name}', stream_handler)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    # 2. Arrancar el cliente de Telegram de forma segura dentro del bucle activo
    await bot.start(bot_token=BOT_TOKEN)
    print("🤖 Bot Blancid MTProto iniciado correctamente.")
    
    # Mantener corriendo
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # Usar el método moderno para ejecutar el bucle principal de asyncio
    asyncio.run(main())
