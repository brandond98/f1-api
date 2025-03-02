from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


async def getCarData():
    url = f"https://api.openf1.org/v1/drivers?&session_key=latest"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        return data


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        carData = await getCarData()
        while True:
            await manager.broadcast(carData)

    except WebSocketDisconnect:
        await manager.send_personal_message("Disconnected", websocket)
        manager.disconnect(websocket)

    except Exception as e:
        print(f"Error: {e}")
