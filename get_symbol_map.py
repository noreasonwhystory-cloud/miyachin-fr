"""
BTCC Symbol List & Mapping 調査
"""
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def get_symbol_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        symbol_list_data = None

        async def handle_response(response):
            nonlocal symbol_list_data
            url = response.url
            if "/v1/market/symbol/list" in url or "/v1/market/symbol-list" in url:
                try:
                    symbol_list_data = await response.json()
                    print(f"Symbol list found at: {url}")
                except:
                    pass

        page.on("response", handle_response)

        try:
            print("BTCCマーケットページへ移動中...")
            await page.goto("https://www.btcc.com/en-US/markets/tradfi", wait_until="networkidle")
            await asyncio.sleep(5)

            if symbol_list_data:
                with open("symbol_list.json", "w", encoding="utf-8") as f:
                    json.dump(symbol_list_data, f, indent=2, ensure_ascii=False)
                print("Symbol list saved to symbol_list.json")
            else:
                print("Symbol list not captured. Trying direct API call simulation...")
                # Try some likely endpoints
                endpoints = [
                    "https://capi.btcc.com/v1/market/symbol/list",
                    "https://capi.btcc.com/v1/market/symbol-list"
                ]
                for ep in endpoints:
                    print(f"Testing {ep}...")
                    res = await page.evaluate(f'fetch("{ep}").then(r => r.json())')
                    if res:
                        with open(f"symbol_list_direct.json", "w", encoding="utf-8") as f:
                            json.dump(res, f, indent=2, ensure_ascii=False)
                        print(f"Direct API call to {ep} succeeded.")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(get_symbol_map())
