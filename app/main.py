import subprocess
import platform
import re
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==========================================
# 动态导入你的各个底层安全组件 (Adapter)
# 加上 try-except 是为了防止你某些模块还没写完导致整个程序崩溃
# ==========================================
try:
    from app.adapters.nsfocus_auto import auto_submit_task
except ImportError:
    def auto_submit_task(target_ip):
        print(f"[-] 尚未完善 nsfocus_auto，假装正在执行绿盟任务: {target_ip}")

try:
    from app.adapters.nmap_adapter import run_nmap
except ImportError:
    def run_nmap(target_ip):
        print(f"[-] 尚未完善 nmap_adapter，假装正在执行 Nmap: {target_ip}")

try:
    from app.adapters.fscan_adapter import run_fscan
except ImportError:
    def run_fscan(target_ip):
        print(f"[-] 尚未完善 fscan_adapter，假装正在执行 Fscan: {target_ip}")

app = FastAPI(title="My Security Toolbox API")

# ==========================================
# 1. 解决跨域 (CORS) 问题（核心！）
# 允许任何本地 HTML 或 Vue 页面调用此后端
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 测试阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许 POST, GET 等所有请求方法
    allow_headers=["*"],  # 允许所有请求头
)


# ==========================================
# 2. 定义前端传来的数据格式约束
# ==========================================
class TargetRequest(BaseModel):
    target_ip: str


class BasicToolRequest(BaseModel):
    tool: str
    target: str


# ==========================================
# 3. 安全防御机制：防命令注入
# ==========================================
def is_valid_target(target: str) -> bool:
    # 只允许字母、数字、点(.)和连字符(-)，彻底杜绝空格、&、|、; 等黑客拼接字符
    pattern = re.compile(r"^[a-zA-Z0-9\.\-]+$")
    return bool(pattern.match(target))


# ==========================================
# 4. 路由接口大全 (对应前端的各个按钮)
# ==========================================

# --- [模块 A] 基础网络工具 (Ping / Tracert) ---
@app.post("/api/basic/run")
def run_basic_tool(req: BasicToolRequest):
    if not is_valid_target(req.target):
        return {"code": 400, "message": "非法的目标地址！检测到注入风险。", "data": ""}

    system = platform.system().lower()

    try:
        # 根据不同操作系统自动适配底层指令
        if req.tool == "ping":
            cmd = ["ping", "-n", "4", req.target] if system == "windows" else ["ping", "-c", "4", req.target]
        elif req.tool == "tracert":
            cmd = ["tracert", "-d", "-h", "15", req.target] if system == "windows" else ["traceroute", "-n", "-m", "15",
                                                                                         req.target]
        else:
            return {"code": 400, "message": "不支持的基础工具", "data": ""}

        # 安全执行命令 (坚决不用 shell=True)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

        # 智能匹配 Windows(默认GBK) 和 Linux(UTF-8) 编码，防止中文乱码
        try:
            output = result.stdout.decode('gbk')
        except UnicodeDecodeError:
            output = result.stdout.decode('utf-8', errors='replace')

        return {"code": 200, "message": f"{req.tool.upper()} 探测执行完毕", "data": output}

    except subprocess.TimeoutExpired:
        return {"code": 500, "message": "执行超时 (已强制切断)", "data": ""}
    except Exception as e:
        return {"code": 500, "message": f"系统底层错误: {str(e)}", "data": ""}


# --- [模块 B] Nmap 扫描接口 ---
@app.post("/api/nmap/scan")
def trigger_nmap(req: TargetRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_nmap, req.target_ip)
    return {"code": 200, "message": f"Nmap 引擎已启动，正在后台探测: {req.target_ip}"}


# --- [模块 C] Fscan 扫描接口 ---
@app.post("/api/fscan/scan")
def trigger_fscan(req: TargetRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_fscan, req.target_ip)
    return {"code": 200, "message": f"Fscan 引擎已启动，正在后台扫雷: {req.target_ip}"}


# --- [模块 D] 绿盟漏扫 自动化下发接口 ---
@app.post("/api/nsfocus/scan")
def trigger_nsfocus_scan(req: TargetRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(auto_submit_task, req.target_ip)
    return {"code": 200, "message": f"自动化浏览器组件已唤醒，正在处理: {req.target_ip}"}


# (可选) 保证直接运行该脚本时能启动服务
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)