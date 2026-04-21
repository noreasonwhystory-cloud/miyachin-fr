"""
BTCC詳細調査スクリプト: ネットワーク通信とDOM構造の解析
"""
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def investigate():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # ネットワークログ
        ws_urls = []
        api_urls = []

        def handle_request(request):
            url = request.url
            if "api" in url or "capi" in url or "v1" in url:
                api_urls.append(url)

        def handle_ws(ws):
            ws_urls.append(ws.url)
            print(f"WebSocket detected: {ws.url}")
            ws.on("framesent", lambda payload: print(f"WS Sent: {payload[:100]}"))
            ws.on("framereceived", lambda payload: print(f"WS Received: {payload[:100]}"))

        page.on("request", handle_request)
        page.on("websocket", handle_ws)

        try:
            print("BTCC XAUUSDページへ移動中...")
            await page.goto("https://www.btcc.com/en-US/trade/tradfi/XAUUSDUSDT", wait_until="networkidle", timeout=60000)
            
            # Cloudflare通過待ち
            for _ in range(10):
                title = await page.title()
                if "Just a moment" in title:
                    print("Cloudflare待機中...")
                    await asyncio.sleep(2)
                else:
                    break
            
            await asyncio.sleep(5) # データの安定を待つ
            
            # DOMダンプ (ヘッダー部分)
            header_html = await page.evaluate('''() => {
                const header = document.querySelector('header') || document.querySelector('[class*="header"]');
                return header ? header.outerHTML : "Header not found";
            }''')
            with open("header_dump.html", "w", encoding="utf-8") as f:
                f.write(header_html)
            
            # スクリーンショット
            await page.screenshot(path="debug_full.png", full_page=True)
            print("調査完了。ファイルを保存しました。")
            
            print("\n--- Detected WebSocket URLs ---")
            for url in set(ws_urls): print(url)
            
            print("\n--- Detected API/CAPI URLs ---")
            for url in set(api_urls[:20]): print(url)

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(investigate())
