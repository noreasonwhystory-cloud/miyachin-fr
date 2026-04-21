"""
デバッグ用: 成功銘柄(XAUUSD)と失敗銘柄(TECH100)のDOM構造を比較するスクリプト
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_page(url, label):
    print(f"\n{'='*60}")
    print(f"デバッグ: {label}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)

            # 1. ページタイトル
            title = await page.title()
            print(f"\nタイトル: {title}")

            # 2. 全ボタンの内容
            buttons = await page.query_selector_all("button")
            print(f"\nボタン数: {len(buttons)}")
            for i, btn in enumerate(buttons):
                text = (await btn.inner_text()).strip()
                if text and len(text) < 100:
                    classes = await btn.get_attribute("class") or ""
                    print(f"  btn[{i}]: text='{text}' class='{classes[:80]}'")

            # 3. "Buy" / "Sell" を含むテキストの探索
            print("\n--- 'Buy' を含む要素 ---")
            buy_els = await page.query_selector_all("text=Buy")
            for el in buy_els[:5]:
                tag = await el.evaluate("el => el.tagName")
                text = (await el.inner_text()).strip()
                parent_text = await el.evaluate("el => el.parentElement ? el.parentElement.innerText.trim().substring(0, 100) : ''")
                print(f"  <{tag}> '{text}' | parent: '{parent_text}'")

            print("\n--- 'Sell' を含む要素 ---")
            sell_els = await page.query_selector_all("text=Sell")
            for el in sell_els[:5]:
                tag = await el.evaluate("el => el.tagName")
                text = (await el.inner_text()).strip()
                parent_text = await el.evaluate("el => el.parentElement ? el.parentElement.innerText.trim().substring(0, 100) : ''")
                print(f"  <{tag}> '{text}' | parent: '{parent_text}'")

            # 4. 数値パターン(価格候補)を含む要素の探索
            print("\n--- 数値パターン探索 (正規表現 Buy/Sell + 数字) ---")
            import re
            content = await page.content()
            buy_matches = re.findall(r'Buy[^<]{0,50}?([\d,]+\.?\d+)', content)
            sell_matches = re.findall(r'Sell[^<]{0,50}?([\d,]+\.?\d+)', content)
            print(f"  Buy+数値マッチ: {buy_matches[:5]}")
            print(f"  Sell+数値マッチ: {sell_matches[:5]}")

            # 5. Cloudflareチェックの検出
            cf_check = await page.query_selector("text=Verify you are human")
            if cf_check:
                print("\n⚠️ Cloudflareキャプチャが検出されました！")
            else:
                print("\n✅ Cloudflareキャプチャなし")

            # 6. スクリーンショット保存
            screenshot_path = f"logs/debug_{label.replace('/', '_')}.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"\nスクリーンショット保存: {screenshot_path}")

        except Exception as e:
            print(f"\nエラー: {e}")
        finally:
            await browser.close()


async def main():
    # 成功銘柄
    await debug_page(
        "https://www.btcc.com/en-US/trade/tradfi/XAUUSDUSDT",
        "XAUUSD (成功銘柄)"
    )
    # 失敗銘柄
    await debug_page(
        "https://www.btcc.com/en-US/trade/tradfi/TECH100USDT",
        "TECH100 (失敗銘柄)"
    )
    # 株式
    await debug_page(
        "https://www.btcc.com/en-US/trade/tradfi/TSLAUSDT",
        "TSLA (株式)"
    )


if __name__ == "__main__":
    asyncio.run(main())
