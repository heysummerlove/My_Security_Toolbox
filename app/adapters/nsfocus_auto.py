from playwright.sync_api import sync_playwright
import time

def auto_submit_task(target_ip):
    with sync_playwright() as p:
        # 1. 启动浏览器（测试时 headless=False 看着它跑，没问题了改成 True 丢后台）
        browser = p.chromium.launch(headless=False)
        
        # 2. 【关键！】创建一个忽略 HTTPS 证书错误的上下文
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            print(f"[*] 正在连接扫描器: https://192.168.93.2/ ...")
            
            # 3. 访问你的漏扫系统
            page.goto("https://192.168.93.2/")
            
            # 等待网络空闲，确保登录框加载出来了
            page.wait_for_load_state("networkidle")

            # -------------------- 登录阶段 --------------------
            print("[*] 正在尝试登录...")
            
            # 注意：这里的定位器可能需要根据实际网页调整（按 F12 看输入框的属性）
            # 尝试一：通过 placeholder 找
            page.get_by_placeholder("用户名").fill("admin") 
            page.get_by_placeholder("密码").fill("Nsfocus@123")
            
            # 如果上面报错找不到，可以换成下面这种 CSS 选择器找法：
            # page.locator("input[name='username']").fill("admin")
            # page.locator("input[type='password']").fill("Nsfocus@123")

            # 点击登录按钮
            page.get_by_text("登录").click()
            # page.locator("button.login-btn").click() # 如果没文字可以用这招

            # 等待登录成功的跳转
            page.wait_for_load_state("networkidle")
            print("[+] 登录成功！")

            # -------------------- 下发任务阶段 --------------------
            print(f"[*] 正在为 {target_ip} 下发扫描任务...")
            
            # 这里的按钮文字你需要自己看着网页改
            page.get_by_text("新建任务").click() 
            time.sleep(1) # 有时候弹窗有动画，稍微等1秒
            
            # 填入你要扫描的 IP
            # page.get_by_placeholder("请输入目标IP").fill(target_ip)
            page.locator("textarea, input").filter(has_text="").first.fill(target_ip) # 这是一个比较暴力的通用填法
            
            # 点击开始/确认
            page.get_by_text("确 定").click()
            # page.get_by_text("开始扫描").click()

            print(f"[+] 目标 {target_ip} 任务下发完成！\n")
            time.sleep(2) # 留点时间让请求发出去

        except Exception as e:
            print(f"[-] 发生错误: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # 测试扫描一个 IP
    auto_submit_task("192.168.93.100")