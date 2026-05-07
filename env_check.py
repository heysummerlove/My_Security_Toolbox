import sys
import socket
import os

print("-> 检查 Python 核心依赖...")
try:
    import fastapi
    import uvicorn
    import pydantic
    print("   [✔] 依赖完整")
except ImportError as e:
    print(f"   [❌] 致命错误: 缺少 {e.name} 库。请检查 runtime 环境是否配置正确！")
    sys.exit(1)

print("-> 检查 API 端口 (8088)...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    if s.connect_ex(('127.0.0.1', 8088)) == 0:
        print("   [❌] 致命错误: 8088 端口已被占用，请关闭冲突程序！")
        sys.exit(1)
print("   [✔] 端口可用")

print("-> 检查武器库目录...")
if not os.path.exists('tools'):
    os.makedirs('tools')
    print("   [⚠️] 自动创建了 /tools 目录，请记得放入 exe 文件")
else:
    print("   [✔] 武器库目录存在")

sys.exit(0)