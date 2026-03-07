import os, time, threading, queue, pygame, sys, glob
from gtts import gTTS
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent

""" if len(sys.argv) < 2:
    print("❌ Uso: python lector_solo_mensaje.py usuario")
    sys.exit(1) """

USER_ID = sys.argv[1].replace("@", "")
speech_queue = queue.Queue()
is_running = True

def cleanup():
    """Borra mp3 residuales con el prefijo de esta versión"""
    for f in glob.glob("temp_s_*.mp3"):
        try: os.remove(f)
        except: pass

def voice_worker():
    pygame.mixer.init()
    while is_running:
        try:
            texto = speech_queue.get(timeout=1)
            if speech_queue.qsize() > 5:
                with speech_queue.mutex: speech_queue.queue.clear()
            
            archivo = f"temp_s_{int(time.time() * 1000)}.mp3"
            gTTS(text=texto, lang='es').save(archivo)
            pygame.mixer.music.load(archivo)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.1)
            pygame.mixer.music.unload()
            if os.path.exists(archivo): os.remove(archivo)
        except queue.Empty: continue
        except: pass

threading.Thread(target=voice_worker, daemon=True).start()
client = TikTokLiveClient(unique_id=f"@{USER_ID}")
processed_ids = set()

@client.on(ConnectEvent)
async def on_connect(event): print(f"✅ Conectado (Solo Mensajes): {event.unique_id}")

@client.on(DisconnectEvent)
async def on_disconnect(event):
    global is_running
    print(f"\n⚠︝ El Live terminó. Limpiando y saliendo..."); is_running = False
    cleanup(); os._exit(0)

@client.on(CommentEvent)
async def on_comment(event):
    msg_id = getattr(event, 'id', f"{event.user.unique_id}_{event.comment}")
    if msg_id in processed_ids: return
    processed_ids.add(msg_id)
    if len(processed_ids) > 100: processed_ids.pop()
    
    print(f"💬 {event.user.nickname}: {event.comment}")
    speech_queue.put(event.comment) # <--- Aquí solo pasamos el comentario

if __name__ == '__main__':
    try: cleanup(); client.run()
    except KeyboardInterrupt: cleanup(); os._exit(0)
