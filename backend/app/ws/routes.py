from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.ws.manager import manager
from app.ws.monitor_store import monitor_store

router = APIRouter()


@router.websocket("/ws/monitor")
async def ws_monitor(
    websocket: WebSocket,
    attempt_id: int | None = Query(default=None),
):
    await manager.connect(websocket)

    # 1) Ulangan zahoti history yuboramiz (yo‘qolmasin!)
    history = monitor_store.list(attempt_id=attempt_id, limit=100)
    await websocket.send_json(
        {
            "type": "history",
            "attempt_id": attempt_id,
            "events": history,
        }
    )

    try:
        while True:
            # teacher tomondan message shart emas, ping sifatida qabul qilamiz
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        print("ws_monitor error:", e)
