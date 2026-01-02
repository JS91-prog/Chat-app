import socketio
from aiohttp import web
import os

# --- CONFIGURATION ---
PORT = int(os.environ.get("PORT", 3001))
MAX_BUFFER = 50 * 1024 * 1024  # 50MB

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*', max_http_buffer_size=MAX_BUFFER)
app = web.Application()
sio.attach(app)

# Dictionary to store {sid: username}
users = {}

# --- ROUTES ---
async def index(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="index.html not found", status=404)

# PWA Routes
async def serve_manifest(request): return web.FileResponse('./manifest.json')
async def serve_sw(request): return web.FileResponse('./sw.js')
async def serve_icon_192(request): return web.FileResponse('./icon-192.png')
async def serve_icon_512(request): return web.FileResponse('./icon-512.png')

app.router.add_get('/', index)
app.router.add_get('/manifest.json', serve_manifest)
app.router.add_get('/sw.js', serve_sw)
app.router.add_get('/icon-192.png', serve_icon_192)
app.router.add_get('/icon-512.png', serve_icon_512)

# --- HELPER FUNCTIONS ---
async def broadcast_user_list():
    """Constructs the list of all connected users and sends it to everyone."""
    user_list = [{"sid": sid, "name": name} for sid, name in users.items()]
    await sio.emit('update_user_list', {'users': user_list, 'count': len(user_list)})

# --- SOCKET EVENTS ---
@sio.event
async def connect(sid, environ):
    print(f"User {sid} connected")

@sio.event
async def join_chat(sid, data):
    username = data.get('username', 'Guest')
    users[sid] = username
    # Send system message
    await sio.emit('receive_message', {'type': 'system', 'content': f'{username} has joined.'})
    # Update user list
    await broadcast_user_list()

@sio.event
async def disconnect(sid):
    if sid in users:
        username = users[sid]
        del users[sid]
        # Notify others
        await sio.emit('receive_message', {'type': 'system', 'content': f'{username} has left.'})
        # Update user list
        await broadcast_user_list()

@sio.event
async def send_message(sid, data):
    await sio.emit('receive_message', data)

# --- TYPING EVENTS ---
@sio.event
async def typing(sid):
    username = users.get(sid, "Someone")
    await sio.emit('display_typing', {'username': username, 'sid': sid}, skip_sid=sid)

@sio.event
async def stop_typing(sid):
    await sio.emit('hide_typing', {'sid': sid}, skip_sid=sid)

# --- WEBRTC EVENTS ---
@sio.event
async def call_user(sid, data):
    await sio.emit('call_made', data, skip_sid=sid)

@sio.event
async def make_answer(sid, data):
    await sio.emit('answer_made', data, skip_sid=sid)

@sio.event
async def ice_candidate(sid, data):
    await sio.emit('ice_candidate', data, skip_sid=sid)

@sio.event
async def end_call(sid):
    await sio.emit('call_ended', {}, skip_sid=sid)

if __name__ == '__main__':
    print(f"🚀 Server starting on port {PORT}...")
    web.run_app(app, host='0.0.0.0', port=PORT)