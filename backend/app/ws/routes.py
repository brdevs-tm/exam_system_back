from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.hub import hub

router = APIRouter()

@router.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            # teacher'dan kelgan msg shart emas, ping sifatida qabul qilamiz
            await ws.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(ws)
