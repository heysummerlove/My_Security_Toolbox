from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import asyncio
import sqlite3
from datetime import datetime
import subprocess
import platform
import re

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




# 确保文件顶部有这些导入，并且已经导入了 BaseModel
# from pydantic import BaseModel

# 1. 定义基础工具的请求体
class BasicToolRequest(BaseModel):
    tool: str
    target: str


# 2. 核心安全防御：严格的正则校验，防止命令注入！
def is_valid_target(target: str) -> bool:
    # 只允许字母、数字、点和连字符，彻底杜绝空格、&、|、; 等恶意字符
    pattern = re.compile(r"^[a-zA-Z0-9\.\-]+$")
    return bool(pattern.match(target))


# 3. 基础网络工具的接口路由
@app.post("/api/basic/run")
def run_basic_tool(req: BasicToolRequest):
    if not is_valid_target(req.target):
        return {"code": 400, "message": "非法的目标地址！检测到非法字符。"}

    system = platform.system().lower()

    try:
        # 根据系统（Windows/Linux）自动选择对应的内置命令
        if req.tool == "ping":
            # Windows 下 ping 4 次，Linux 下 ping 4 次
            cmd = ["ping", "-n", "4", req.target] if system == "windows" else ["ping", "-c", "4", req.target]
        elif req.tool == "tracert":
            # 限制最大跃点数为 15，防止卡死
            cmd = ["tracert", "-d", "-h", "15", req.target] if system == "windows" else ["traceroute", "-n", "-m", "15",
                                                                                         req.target]
        else:
            return {"code": 400, "message": "不支持的工具"}

        # 安全执行命令 (强制使用列表传参，绝对不使用 shell=True)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

        # 兼容 Windows(通常是 GBK) 和 Linux(UTF-8) 的控制台输出编码
        try:
            output = result.stdout.decode('gbk')
        except UnicodeDecodeError:
            output = result.stdout.decode('utf-8', errors='replace')

        return {"code": 200, "message": f"{req.tool.upper()} 执行完毕", "data": output}

    except subprocess.TimeoutExpired:
        return {"code": 500, "message": "执行超时 (已强制中断)"}
    except Exception as e:
        return {"code": 500, "message": f"执行错误: {str(e)}"}