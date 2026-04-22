"""
BTCC Tradfiスプレッド調査ツール - スクレイパー（WebSocket傍受方式）
================================================================
ブラウザで1つの取引ページを開き、裏側で通信されているWebSocketを傍受して
全銘柄のリアルタイム価格を取得する。

メリット:
- 低速なページ操作（クリック・検索）が不要。
- Cloudflareチャレンジ通過後は非常に安定する。
- 数秒で全銘柄の価格を最新化できる。
"""

import time
import json
import asyncio
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import (
    BTCC_BASE_URL,
    HEADLESS,
    PAGE_LOAD_TIMEOUT_SECONDS,
    get_all_symbols,
)


@dataclass
class SpreadData:
    """1銘柄のスプレッドデータ"""
    symbol: str
    name: str
    category: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    spread_pct: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: float = 0.0


class BTCCScraper:
    """WebSocketを傍受して全Tradfi銘柄の価格を取得するスクレイパー"""

    def __init__(self, sys_logger):
        self.sys_logger = sys_logger
        # 最新価格のバッファ { "SYMBOL": SpreadData }
        self._price_buffer: Dict[str, SpreadData] = {}
        self._symbols_map = {s["symbol"]: s for s in get_all_symbols()}
        self._secid_map: Dict[str, str] = {} # SecID -> Symbol mapping
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._ws_connected = False

    async def start(self):
        """ブラウザを起動し、WebSocketを直接操作して全銘柄の購読を開始する"""
        self.sys_logger.info("ブラウザを起動中（WebSocketインジェクションモード）...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        self._page = await self._context.new_page()

        # WebSocketインスタンスを捕捉するためのインジェクション
        await self._page.add_init_script("""
            window._btcc_ws = [];
            const _NativeWS = window.WebSocket;
            window.WebSocket = function(...args) {
                const ws = new _NativeWS(...args);
                window._btcc_ws.push(ws);
                return ws;
            };
        """)

        # WebSocketイベントハンドラを登録
        self._page.on("websocket", self._handle_websocket)

        # 代表ページに移動
        try:
            url = "https://www.btcc.com/en-US/trade/tradfi/AAPLUSDT"
            self.sys_logger.info(f"取引ページに遷移中: {url}")
            await self._page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # マッピング情報 (Dict) が来るのを待つ
            # ページロード後、自動的に Dict が流れてくるはず
            await asyncio.sleep(8)
            
            # 購読メッセージを送信
            await self._trigger_bulk_subscription()

            await asyncio.sleep(5)
            self.sys_logger.info("購読完了。リアルタイム更新を受信中...")
        except Exception as e:
            self.sys_logger.error(f"初期ロードエラー: {e}")

    async def _trigger_bulk_subscription(self):
        """全てのTradFi銘柄の購読メッセージをWebSocketに送り込む"""
        if not self._secid_map:
            self.sys_logger.warning("マッピング未完了のため購読をスキップします。")
            return

        secids = [sid for sid, sym in self._secid_map.items() if sym in self._symbols_map]
        
        if not secids:
            self.sys_logger.warning("対象のSecIDが見つかりませんでした。")
            return

        # 購読フレームの作成
        main_id = secids[0]
        # symbolsfrequency に全IDを入れることで全銘柄のリアルタイム配信を促す
        msg = {
            "action": "ReqSubcri",
            "symbols": [main_id],
            "symbolsfrequency": secids,
            "deep": main_id,
            "interval": 1
        }
        
        self.sys_logger.info(f"バルク購読を送信中: {len(secids)}銘柄")
        
        # ブラウザ側の全WSインスタンスに対してメッセージを送信
        await self._page.evaluate(f"""
            const msg = {json.dumps(msg)};
            window._btcc_ws.forEach(ws => {{
                if (ws.readyState === 1) {{ // OPEN
                    ws.send(JSON.stringify(msg));
                }}
            }});
        """)

    def _handle_websocket(self, ws):
        """WebSocket通信の解析"""
        self.sys_logger.info(f"WebSocket 接続を検出: {ws.url}")
        self._ws_connected = True
        ws.on("framereceived", self._on_message)

    def _on_message(self, payload):
        """価格データのパース"""
        try:
            if isinstance(payload, bytes):
                try:
                    data = json.loads(payload.decode('utf-8'))
                except:
                    return
            else:
                data = json.loads(payload)

            action = data.get("action")
            
            # 1. マッピング情報の取得 (action: Dict)
            if action == "Dict":
                dict_info = data.get("data", {}).get("DictInfo", [])
                initial_map_size = len(self._secid_map)
                
                for item in dict_info:
                    secid = str(item.get("SecID"))
                    short_name = str(item.get("ShortName", ""))
                    
                    # より堅牢なシンボル抽出
                    # 例: "AAPL/USDT.50x" -> "AAPL", "GER30/USDX.150x" -> "GER30"
                    base_symbol = short_name.split('/')[0].split('.')[0]
                    symbol_upper = base_symbol.upper()
                    
                    # "AAPLUSDT" などの連結形式にも対応
                    if symbol_upper.endswith("USDT") and len(symbol_upper) > 4:
                        symbol_upper = symbol_upper[:-4]
                    
                    self._secid_map[secid] = symbol_upper
                
                # 新しいマッピングが見つかった場合、購読を再発行（重要）
                if len(self._secid_map) > initial_map_size:
                    found_symbols = [s for s in self._secid_map.values() if s in self._symbols_map]
                    self.sys_logger.info(f"SecIDマッピング更新: {len(self._secid_map)}件登録 (対象ヒット: {len(set(found_symbols))}/{len(self._symbols_map)})")
                    # 非同期タスクとして購読トリガーを実行
                    asyncio.create_task(self._trigger_bulk_subscription())
                return

            # 2. 価格情報の更新 (action: tickinfo)
            if action == "tickinfo":
                ticker_list = data.get("data", [])
                for item in ticker_list:
                    secid = str(item.get("Y"))
                    symbol = self._secid_map.get(secid)
                    
                    if symbol and symbol in self._symbols_map:
                        # 複数のBid/Askから最良値を取得
                        bids = item.get("B", [])
                        asks = item.get("A", [])
                        
                        if bids and asks:
                            try:
                                bid = float(bids[0])
                                ask = float(asks[0])
                                
                                if bid > 0 and ask > 0:
                                    info = self._symbols_map[symbol]
                                    spread = round(ask - bid, 6)
                                    mid = (ask + bid) / 2
                                    spread_pct = round((spread / mid) * 100, 6) if mid > 0 else 0.0
                                    
                                    # データクラスを使用して保存
                                    self._price_buffer[symbol] = SpreadData(
                                        symbol=symbol,
                                        name=info["name"],
                                        category=info["category"],
                                        bid=bid,
                                        ask=ask,
                                        spread=spread,
                                        spread_pct=spread_pct,
                                        success=True,
                                        timestamp=time.time()
                                    )
                            except (ValueError, TypeError):
                                continue
        except Exception as e:
            self.sys_logger.error(f"WSデータ処理エラー: {e}")

    async def get_all_spreads(self) -> List[SpreadData]:
        """バッファにある全ての銘柄の最新スプレッドを返す"""
        # データが揃うまで最大15秒待つ
        wait_start = time.time()
        self.sys_logger.info(f"価格データ収集中... (現在取得済み: {len(self._price_buffer)}/{len(self._symbols_map)})")
        
        while len(self._price_buffer) < len(self._symbols_map):
            if time.time() - wait_start > 15:
                break
            await asyncio.sleep(0.5)
        
        self.sys_logger.info(f"データ収集完了: {len(self._price_buffer)}銘柄取得")

        results = []
        for symbol, info in self._symbols_map.items():
            if symbol in self._price_buffer:
                results.append(self._price_buffer[symbol])
            else:
                results.append(SpreadData(
                    symbol=symbol,
                    name=info["name"],
                    category=info["category"],
                    success=False,
                    error="No WS data"
                ))
        
        return results

    async def stop(self):
        """ブラウザを終了する"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self.sys_logger.info("ブラウザ終了")
