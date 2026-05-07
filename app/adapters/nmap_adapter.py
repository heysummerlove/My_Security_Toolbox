import asyncio
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXE_PATH = os.path.join(BASE_DIR, 'tools', 'nmap', 'nmap.exe')
DB_PATH = os.path.join(BASE_DIR, 'data', 'toolbox.db')


def update_status(task_id, status_msg):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE tasks SET status = ?, update_time = ? WHERE id = ?",
                 (status_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id))
    conn.commit()
    conn.close()


async def run_nmap(task_id: int, target: str):
    if not os.path.exists(EXE_PATH):
        update_status(task_id, "ERROR: 未找到 nmap.exe")
        return

    # 这里放真实的 Nmap 调用逻辑，结构和 fscan_adapter 一样
    update_status(task_id, "COMPLETED: 端口探测完成 (请补充 Nmap 调用代码)")