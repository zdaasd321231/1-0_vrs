from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime
import subprocess
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class VNCSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    display_id: int
    port: int
    websocket_port: int
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VNCSessionCreate(BaseModel):
    display_id: int = Field(default=1, ge=1, le=99)
    geometry: str = Field(default="1024x768")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/vnc/sessions", response_model=VNCSession)
async def create_vnc_session(session_data: VNCSessionCreate):
    """Создать новую VNC сессию"""
    try:
        display_port = 5900 + session_data.display_id
        websocket_port = 6080 + session_data.display_id - 1
        
        # Запустить VNC сервер
        cmd = f"export USER=root && vncserver :{session_data.display_id} -geometry {session_data.geometry} -depth 24"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Возможно сессия уже существует, попробуем убить и пересоздать
            subprocess.run(f"export USER=root && vncserver -kill :{session_data.display_id}", shell=True)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Запустить websockify для этой сессии
        websockify_cmd = f"cd /app/noVNC && websockify --web . {websocket_port} localhost:{display_port} > websockify_{session_data.display_id}.log 2>&1 &"
        subprocess.run(websockify_cmd, shell=True)
        
        session = VNCSession(
            display_id=session_data.display_id,
            port=display_port,
            websocket_port=websocket_port,
            status="active"
        )
        
        # Сохранить в базу данных
        await db.vnc_sessions.insert_one(session.dict())
        
        return session
    except Exception as e:
        logger.error(f"Error creating VNC session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create VNC session: {str(e)}")

@api_router.get("/vnc/sessions", response_model=List[VNCSession])
async def get_vnc_sessions():
    """Получить список всех VNC сессий"""
    sessions = await db.vnc_sessions.find().to_list(1000)
    return [VNCSession(**session) for session in sessions]

@api_router.get("/vnc/sessions/{session_id}")
async def get_vnc_session(session_id: str):
    """Получить информацию о конкретной VNC сессии"""
    session = await db.vnc_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="VNC session not found")
    return VNCSession(**session)

@api_router.delete("/vnc/sessions/{session_id}")
async def delete_vnc_session(session_id: str):
    """Удалить VNC сессию"""
    session = await db.vnc_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="VNC session not found")
    
    try:
        # Остановить VNC сервер
        subprocess.run(f"export USER=root && vncserver -kill :{session['display_id']}", shell=True)
        
        # Остановить websockify
        subprocess.run(f"pkill -f 'websockify.*{session['websocket_port']}'", shell=True)
        
        # Удалить из базы данных
        await db.vnc_sessions.delete_one({"id": session_id})
        
        return {"message": "VNC session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting VNC session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete VNC session: {str(e)}")

@api_router.get("/vnc/connect/{session_id}")
async def get_vnc_connection_info(session_id: str):
    """Получить информацию для подключения к VNC сессии"""
    session = await db.vnc_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="VNC session not found")
    
    return {
        "vnc_url": f"vnc://localhost:{session['port']}",
        "websocket_url": f"ws://localhost:{session['websocket_port']}",
        "novnc_url": f"http://localhost:{session['websocket_port']}/vnc.html?host=localhost&port={session['websocket_port']}&password=vncpassword",
        "display_id": session['display_id'],
        "password": "vncpass"  # Простой пароль для демонстрации
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
