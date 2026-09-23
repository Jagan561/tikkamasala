"""
WebSocket endpoint for real-time order updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import ws_manager
from app.utils.jwt import decode_token

router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/ws/orders")
async def websocket_orders(websocket: WebSocket, token: str = Query(...)):
    """
    Connect as customer or admin.
    Customers receive events for their own orders.
    Admins receive all new order + status events.
    """
    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    role = payload.get("role", "")
    user_id = int(payload.get("sub", 0))
    is_admin = role in ("admin", "superadmin")

    if is_admin:
        await ws_manager.connect_admin(websocket)
    else:
        await ws_manager.connect_customer(websocket, user_id)

    try:
        while True:
            # Keep connection alive; clients can send ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"pong"}')
    except WebSocketDisconnect:
        if is_admin:
            ws_manager.disconnect(websocket, is_admin=True)
        else:
            ws_manager.disconnect(websocket, user_id=user_id)
