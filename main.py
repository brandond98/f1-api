import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx

BASE_API_URL = "https://api.openf1.org/v1"

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
        try:
            await websocket.send_json(message)
        except RuntimeError:
            pass

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


async def getSessionData(session_key):
    url = f"{BASE_API_URL}/sessions?session_key={session_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()

        session_data = data[0]

        session = {
            "circuit_short_name": session_data.get("circuit_short_name"),
            "date_start": session_data.get("date_start"),
            "location": session_data.get("location"),
            "session_name": session_data.get("session_name"),
            "session_type": session_data.get("session_type"),
        }
        return session


async def getDriverData(session_key):
    url = f"{BASE_API_URL}/drivers?&session_key={session_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        drivers = []

        for driver in data:
            drivers.append(
                {
                    "driver_number": driver.get("driver_number"),
                    "team_colour": driver.get("team_colour"),
                    "name_acronym": driver.get("name_acronym"),
                    "full_name": driver.get("full_name"),
                    "team_name": driver.get("team_name"),
                }
            )
        return drivers


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                drivers = await getDriverData("latest")
                session = await getSessionData("latest")

                await manager.broadcast({"drivers": drivers, "session": session}),

                print("Broadcasted data")

                await asyncio.sleep(3)

            except Exception as e:
                print(f"Broadcast error: {e}")
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        print(f"Websocket error: {e}")
