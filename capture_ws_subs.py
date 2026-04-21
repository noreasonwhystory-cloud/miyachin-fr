"""
BTCC WS Subscription Payload 調査
"""
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def capture_ws_subs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        sent_frames = []
        received_frames = []

        def handle_ws(ws):
            print(f"WS Connected: {ws.url}")
            ws.on("framesent", lambda payload: sent_frames.append(payload))
            ws.on("framereceived", lambda payload: received_frames.append(payload))

        page.on("websocket", handle_ws)

        try:
            print("BTCC XAUUSDページへ移動中...")
            await page.goto("https://www.btcc.com/en-US/trade/tradfi/XAUUSDUSDT", wait_until="networkidle")
            
            # Wait for some time to capture heartbeats and subscriptions
            await asyncio.sleep(20)

            print("\n--- SENT FRAMES ---")
            for frame in sent_frames:
                print(frame)

            # Extract Symbol Info from WS received if possible
            # Often, the first few frames contain symbol metadata
            print("\n--- ANALYZING RECEIVED FRAMES FOR METADATA ---")
            for frame in received_frames:
                if '"action":"tickinfo"' in frame:
                    # We already know this format, let's look for others
                    continue
                if len(frame) > 100:
                    print(f"Large frame received ({len(frame)} bytes)")
                    if '"symbol"' in frame.lower():
                        print("SYMBOL DATA DETECTED!")
                        with open("ws_symbol_data_candidate.json", "w", encoding="utf-8") as f:
                            f.write(frame)

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_ws_subs())
