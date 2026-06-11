"""
拉钩招聘 - 自动过阿里云WAF滑块验证码 + 获取Cookie
  策略：先尝试自动模拟滑动，失败则弹窗让人工操作
"""
import asyncio
import json
import random
from pathlib import Path

from playwright.async_api import async_playwright

OUTPUT = Path(__file__).parent / "lagou_cookies.json"

# ==================== 滑块模拟 ====================

async def simulate_human_drag(page):
    """
    模拟人类拖动滑块，绕过阿里云WAF验证码
    阿里云滑块在页面内（非iframe），结构为 .nc-container 内的 #aliyunCaptcha-sliding-slider
    """
    print("[滑块] 检测中...")

    # Step 1：等验证码容器出现
    selectors = [
        "#captcha-element",
        ".nc-container",
        ".nc_wrapper",
    ]
    found = None
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            found = sel
            break
        except Exception:
            continue

    if not found:
        print("[滑块] 未检测到验证码容器（可能已通过）")
        return True

    print(f"[滑块] 检测到验证码容器: {found}")

    # Step 2：等阿里云滑块 iframe/元素加载
    # 阿里云验证码可能加载在 iframe 内或直接内嵌
    # 先检查页面是否已有 slider
    await asyncio.sleep(2)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 尝试找滑块按钮（阿里云验证码的滑块元素）
            slider_sel = "#aliyunCaptcha-sliding-slider"
            slider = await page.query_selector(slider_sel)
            if not slider:
                # 可能在 iframe 里
                frames = page.frames
                for f in frames:
                    slider = await f.query_selector(slider_sel)
                    if slider:
                        print(f"[滑块] 在 iframe 中找到滑块")
                        break

            if not slider:
                # 再试另一种选择器
                slider_sel = ".nc_iconfont"
                slider = await page.query_selector(slider_sel)
                if not slider:
                    for f in page.frames:
                        slider = await f.query_selector(slider_sel)
                        if slider:
                            break

            if not slider:
                print(f"[滑块] 第 {attempt + 1} 次未找到滑块元素，重试...")
                await asyncio.sleep(2)
                continue

            # Step 3：获取滑块和轨道的尺寸
            box = await slider.bounding_box()
            if not box:
                print("[滑块] 无法获取滑块位置")
                continue

            print(f"[滑块] 滑块位置: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

            # 轨道通常在滑块父容器中，需要拖到轨道最右端
            # 阿里云滑块需要拖动大约 300-360px（从CSS可知 width:360）
            # 实际滑动距离 = 轨道宽度 - 滑块宽度 + 一些偏移
            parent = await slider.evaluate("el => el.parentElement")
            if parent:
                parent_box = await page.evaluate("""
                    (el) => {
                        const r = el.getBoundingClientRect();
                        return {x: r.x, y: r.y, w: r.width, h: r.height};
                    }
                """, parent)
                if parent_box:
                    print(f"[滑块] 轨道: w={parent_box['w']:.0f}")
                    # 滑块通常从轨道左边缘开始
                    drag_distance = parent_box["w"] - box["width"] + random.randint(-5, 5)
                else:
                    drag_distance = 300 + random.randint(-10, 10)
            else:
                drag_distance = 300 + random.randint(-10, 10)

            print(f"[滑块] 计划拖动距离: {drag_distance:.0f}px")

            # Step 4：模拟人类拖动（分多段，带随机偏移和速度变化）
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2

            await page.mouse.move(start_x, start_y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.mouse.down()

            # 分 20-30 段拖动，模拟人类轨迹
            steps = random.randint(20, 30)
            current_x = 0
            for step in range(steps):
                # 变速：先快后慢
                progress = step / steps
                if progress < 0.6:
                    # 前60% 加速阶段
                    increment = drag_distance / steps * (1.0 + random.uniform(-0.1, 0.4))
                else:
                    # 后40% 减速阶段
                    increment = drag_distance / steps * (0.4 + random.uniform(-0.1, 0.2))

                current_x += increment
                # Y 轴加入微小随机偏移
                target_x = start_x + min(current_x, drag_distance)
                target_y = start_y + random.uniform(-2, 2)

                await page.mouse.move(target_x, target_y)
                # 随机间隔
                await asyncio.sleep(random.uniform(0.005, 0.03))

            # 最后拖到终点
            await page.mouse.move(start_x + drag_distance, start_y + random.uniform(-2, 2))
            await asyncio.sleep(random.uniform(0.1, 0.2))
            await page.mouse.up()

            print(f"[滑块] 第 {attempt + 1} 次滑动完成，等待验证结果...")
            await asyncio.sleep(3)

            # Step 5：检查是否通过
            still_waf = await page.query_selector("#captcha-element, .nc-container, .nc_wrapper")
            job_list = await page.query_selector("#jobList")

            if job_list:
                print("[滑块] ✅ 验证通过！页面正常加载")
                return True
            elif still_waf:
                # 检查是否有刷新按钮（阿里云验证失败会显示刷新按钮）
                refresh_btn = await page.query_selector(".nc-lang-cnt .nc_refresh, .errloading, .nc_erro")
                if refresh_btn:
                    print(f"[滑块] ❌ 第 {attempt + 1} 次验证失败，点击刷新...")
                    await refresh_btn.click()
                    await asyncio.sleep(2)
                    continue
                else:
                    print(f"[滑块] ❌ 第 {attempt + 1} 次验证失败，等待重试...")
                    await asyncio.sleep(2)
                    continue
            else:
                print("[滑块] 页面状态不确定，可能已通过")
                return True

        except Exception as e:
            print(f"[滑块] 第 {attempt + 1} 次出错: {e}")
            await asyncio.sleep(2)
            continue

    print("[滑块] 自动滑动 3 次均失败")
    return False


# ==================== 主流程 ====================

async def get_cookies() -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,   # 无头模式滑块模拟容易被检测，有头模式更稳
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        )

        # 反检测
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh','en']});
            window.chrome = { runtime: {} };

            // 覆盖 permissions 查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)

        page = await context.new_page()
        print("[访问] https://www.lagou.com/wn/zhaopin/")
        await page.goto("https://www.lagou.com/wn/zhaopin/", wait_until="domcontentloaded", timeout=30000)

        # 检查是否需要过滑块
        is_waf = await page.query_selector("#captcha-element, .nc-container, .nc_wrapper")

        if is_waf:
            print("[WAF] 检测到滑块验证码")

            # 尝试自动滑动
            success = await simulate_human_drag(page)

            if not success:
                # 自动滑动失败，让人工操作
                print("\n" + "=" * 55)
                print("  自动滑动失败，请在弹出的浏览器窗口中手动滑动")
                print("  等待 120 秒...")
                print("=" * 55)
                try:
                    await page.wait_for_selector("#jobList", timeout=120000)
                    print("[WAF] ✅ 人工验证通过")
                except Exception:
                    print("[WAF] ❌ 人工验证超时")
                    await browser.close()
                    return {}
        else:
            # 可能已经通过了（Cookie有效）
            try:
                await page.wait_for_selector("#jobList", timeout=10000)
                print("[页面] ✅ 直接加载成功（无需验证）")
            except Exception:
                print("[页面] ⚠ 页面加载异常")

        # 等待 JS 完全执行，动态 Cookie 全部写入
        print("[等待] JS 执行中，等待动态 Cookie 生成...")
        await asyncio.sleep(5)

        # 检查页面最终状态
        title = await page.title()
        has_joblist = await page.query_selector("#jobList") is not None
        print(f"[页面] 标题: '{title}' | jobList: {has_joblist}")

        # 收集所有 Cookie
        raw = await context.cookies()
        await browser.close()

        cookie_dict = {}
        for c in raw:
            cookie_dict[c["name"]] = c["value"]

        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(cookie_dict, f, ensure_ascii=False, indent=2)

        print(f"\n[完成] 共获取 {len(cookie_dict)} 个 Cookie")
        for k, v in cookie_dict.items():
            head = v[:60] + ("..." if len(v) > 60 else "")
            print(f"  {k} = {head}")

        return cookie_dict


if __name__ == "__main__":
    cookies = asyncio.run(get_cookies())

    if cookies:
        header_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        print(f"\n[Cookie Header 字符串]:\n{header_str[:500]}...")
