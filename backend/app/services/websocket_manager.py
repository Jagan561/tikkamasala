"""
WebSocket connection manager for real-time order updates.
"""
import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # customer_id -> list of WebSocket connections
        self.customer_connections: Dict[int, List[WebSocket]] = {}
        # admin WebSocket connections
        self.admin_connections: List[WebSocket] = []

    async def connect_customer(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.customer_connections:
            self.customer_connections[user_id] = []
        self.customer_connections[user_id].append(websocket)
        logger.info(f"Customer {user_id} connected via WebSocket")

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)
        logger.info("Admin connected via WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: int = None, is_admin: bool = False):
        if is_admin and websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
            logger.info("Admin disconnected from WebSocket")
        elif user_id and user_id in self.customer_connections:
            conns = self.customer_connections[user_id]
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                del self.customer_connections[user_id]
            logger.info(f"Customer {user_id} disconnected from WebSocket")

    async def send_to_customer(self, user_id: int, data: dict):
        """Send a message to all connections of a specific customer."""
        connections = self.customer_connections.get(user_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.remove(ws)

    async def broadcast_to_admins(self, data: dict):
        """Broadcast a message to all connected admins."""
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.admin_connections.remove(ws)


# Singleton instance used across the application
ws_manager = ConnectionManager()
