from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
from loguru import logger
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.dashboard_connections: List[WebSocket] = []
        self.agent_connections: Dict[str, WebSocket] = {}

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.dashboard_connections.append(websocket)
        logger.info(f"Dashboard client connected. Total dashboards: {len(self.dashboard_connections)}")

    def disconnect_dashboard(self, websocket: WebSocket):
        if websocket in self.dashboard_connections:
            self.dashboard_connections.remove(websocket)
            logger.info("Dashboard client disconnected.")

    async def connect_agent(self, websocket: WebSocket, peserta_id: str):
        await websocket.accept()
        self.agent_connections[peserta_id] = websocket
        logger.info(f"Agent {peserta_id} connected.")

    def disconnect_agent(self, peserta_id: str):
        if peserta_id in self.agent_connections:
            del self.agent_connections[peserta_id]
            logger.info(f"Agent {peserta_id} disconnected.")

    async def broadcast_to_dashboards(self, message: dict):
        msg_str = json.dumps(message)
        for connection in self.dashboard_connections:
            try:
                await connection.send_text(msg_str)
            except Exception as e:
                logger.error(f"Error broadcasting to dashboard: {e}")
                
    async def request_screenshot(self, peserta_id: str):
        if peserta_id in self.agent_connections:
            try:
                await self.agent_connections[peserta_id].send_text(json.dumps({"action": "capture"}))
                logger.info(f"Requested screenshot from {peserta_id}")
            except Exception as e:
                logger.error(f"Failed to request screenshot from {peserta_id}: {e}")

    async def send_warning(self, peserta_id: str, message: str):
        if peserta_id in self.agent_connections:
            try:
                await self.agent_connections[peserta_id].send_text(json.dumps({"action": "warning", "message": message}))
                logger.info(f"Sent warning to {peserta_id}")
            except Exception as e:
                logger.error(f"Failed to send warning to {peserta_id}: {e}")

manager = ConnectionManager()

@router.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect_dashboard(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WS message: {data}") # Debug log
            try:
                payload = json.loads(data)
                if payload.get("action") == "peek_screen" and payload.get("peserta_id"):
                    await manager.request_screenshot(str(payload["peserta_id"]))
                elif payload.get("action") == "send_warning" and payload.get("peserta_id"):
                    await manager.send_warning(str(payload["peserta_id"]), payload.get("message", "Peringatan!"))
            except json.JSONDecodeError:
                if data == "ping":
                    await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)

@router.websocket("/ws/stream/{peserta_id}")
async def agent_stream_endpoint(websocket: WebSocket, peserta_id: str):
    await manager.connect_agent(websocket, peserta_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "screenshot":
                    payload["peserta_id"] = peserta_id
                    await manager.broadcast_to_dashboards(payload)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect_agent(peserta_id)
    except Exception as e:
        logger.error(f"Error in agent stream {peserta_id}: {e}")
        manager.disconnect_agent(peserta_id)
