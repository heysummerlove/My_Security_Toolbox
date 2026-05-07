from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import asyncio
import sqlite3
from datetime import datetime

from app.adapters.fscan_adapter import run_fscan
from app.adapters.nmap_adapter import run_nmap

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'toolbox.db')

# 初始化数据库
os.makedirs(DATA_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        target
                        TEXT,
                        tool
                        TEXT,
                        status
                        TEXT,
                        update_time
                        TEXT
                    )''')
    conn.commit()
    conn.close()


init_db()


class TaskRequest(BaseModel):
    target: str
    tool_type: str


@app.get("/api/tasks")
def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return {"status": "success", "data": [dict(t) for t in tasks]}


@app.post("/api/tasks/run")
async def create_task(req: TaskRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO tasks (target, tool, status, update_time) VALUES (?, ?, ?, ?)",
                   (req.target, req.tool_type, "RUNNING...", now))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 路由分发
    if req.tool_type == "FSCAN":
        asyncio.create_task(run_fscan(task_id, req.target))
    elif req.tool_type == "NMAP":
        asyncio.create_task(run_nmap(task_id, req.target))

    return {"status": "success"}


@app.get("/")
def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")