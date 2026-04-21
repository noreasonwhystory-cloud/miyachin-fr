import asyncio
import json
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def debug_ws():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        frames = []
        def handle_ws(ws):
            print(f"Connected to WS: {ws.url}")
            ws.on("framereceived", lambda payload: frames.append(payload))
            
        page.on("websocket", handle_ws)
        
        print("Navigating to Markets page...")
        # TradFiタブを明示的に指定
        try:
            await page.goto("https://www.btcc.com/en-US/markets?tab=tradfi", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Navigation warning (continuing): {e}")
        
        # Cloudflare通過待ち
        await asyncio.sleep(15)
        
        print("Waiting for data (30s)...")
        await asyncio.sleep(30)
        
        print(f"Captured {len(frames)} frames. Saving to ws_dump.txt...")
        with open("ws_dump.txt", "w", encoding="utf-8") as f:
            for frame in frames:
                if isinstance(frame, bytes):
                    try:
                        # GZIPなどの可能性もあるがまずはUTF-8
                        f.write(frame.decode('utf-8') + "\n---\n")
                    except:
                        f.write(f"<binary data: {len(frame)} bytes>\n---\n")
                else:
                    f.write(str(frame) + "\n---\n")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_ws())
