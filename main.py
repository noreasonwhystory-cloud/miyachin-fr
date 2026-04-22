"""
BTCC Tradfiスプレッド調査ツール - メインスクリプト
=================================================
全Tradfi銘柄のBid/Askスプレッドを定期的に取得し、
3日間ローテーションのログファイルに記録する。

使い方:
  python main.py              # 通常の連続実行モード
  python main.py --once       # 1回だけ実行して終了（テスト用）
"""

import sys
import signal
import asyncio
import json
import os
from datetime import datetime
from dataclasses import asdict

from config import POLLING_INTERVAL_SECONDS, JST, get_all_symbols, LOG_DIR
from logger_setup import setup_logger, setup_system_logger
from scraper import BTCCScraper


# ─── グレースフルシャットダウン用フラグ ───
_shutdown_requested = False


def _signal_handler(signum, frame):
    """SIGINT/SIGTERM を受け取ったらフラグを立てる"""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n⚠️  シャットダウン要求を受信しました。現在のサイクル完了後に終了します...")


async def run_cycle(scraper: BTCCScraper, spread_logger, sys_logger):
    """
    1サイクル分の全銘柄スプレッド取得を実行し、ログに記録する。
    """
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    sys_logger.info(f"--- サイクル開始: {now} ---")

    # 決算日および金利の読み込み
    earnings_map = {}
    rollover_map = {}
    
    earnings_path = os.path.join(LOG_DIR, "earnings.json")
    if os.path.exists(earnings_path):
        try:
            with open(earnings_path, "r", encoding="utf-8") as f:
                earning_data = json.load(f)
                earnings_map = earning_data.get("data", {})
        except Exception as e:
            sys_logger.error(f"決算データ読み込み失敗: {e}")

    rollover_path = os.path.join(LOG_DIR, "rollover_fees.json")
    if os.path.exists(rollover_path):
        try:
            with open(rollover_path, "r", encoding="utf-8") as f:
                rollover_data = json.load(f)
                # デフォルトレートまたはカテゴリ別レートを取得
                default_rate = rollover_data.get("default_rate", 0.0002)
                rollover_map = rollover_data.get("category_rates", {})
        except Exception as e:
            sys_logger.error(f"金利データ読み込み失敗: {e}")

    results = await scraper.get_all_spreads()

    # メタデータのマージ (決算日 & 金利)
    for r in results:
        if r.symbol in earnings_map:
            r.earnings_date = earnings_map[r.symbol]
        # カテゴリに基づいて金利を設定
        r.rollover_fee = rollover_map.get(r.category, 0.0002)

    # ログ出力
    for r in results:
        if r.success:
            # スプレッドデータをパイプ区切りで記録
            timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
            line = (
                f"{timestamp} | {r.symbol:10s} | {r.name:12s} | "
                f"Bid: {r.bid:>12} | Ask: {r.ask:>12} | "
                f"Spread: {r.spread:>10} | {r.spread_pct:>8}%"
            )
            if r.earnings_date:
                line += f" | Earnings: {r.earnings_date}"
            if r.rollover_fee:
                line += f" | Rollover: {r.rollover_fee * 100:.3f}%"
            spread_logger.info(line)
        else:
            timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
            spread_logger.info(
                f"{timestamp} | {r.symbol:10s} | {r.name:12s} | "
                f"ERROR: {r.error}"
            )

    # JSON保存 (ダッシュボード用)
    latest_json_path = os.path.join(LOG_DIR, "latest.json")
    try:
        json_data = {
            "last_updated": now,
            "results": [asdict(r) for r in results]
        }
        with open(latest_json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        sys_logger.error(f"JSON保存エラー: {e}")

    # サマリー
    success = sum(1 for r in results if r.success)
    failed = len(results) - success
    sys_logger.info(
        f"--- サイクル完了: 成功={success}, 失敗={failed} ---"
    )

    return results


async def main():
    """メインエントリポイント"""
    # ─── 引数チェック ───
    once_mode = "--once" in sys.argv

    # ─── シグナルハンドラ設定 ───
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # ─── ロガー初期化 ───
    spread_logger = setup_logger()
    sys_logger = setup_system_logger()

    # ─── 起動メッセージ ───
    symbols = get_all_symbols()
    sys_logger.info("=" * 60)
    sys_logger.info("BTCC Tradfiスプレッド調査ツール 起動")
    sys_logger.info(f"  対象銘柄数: {len(symbols)}")
    sys_logger.info(f"  ポーリング間隔: {POLLING_INTERVAL_SECONDS}秒")
    sys_logger.info(f"  モード: {'1回実行' if once_mode else '連続実行'}")
    sys_logger.info("=" * 60)

    # ─── スクレイパー起動 ───
    scraper = BTCCScraper(sys_logger)
    try:
        await scraper.start()

        while True:
            # 1サイクル実行
            await run_cycle(scraper, spread_logger, sys_logger)

            # 1回モードなら終了
            if once_mode:
                sys_logger.info("1回実行モード: 完了しました。")
                break

            # シャットダウン要求チェック
            if _shutdown_requested:
                sys_logger.info("シャットダウン要求により終了します。")
                break

            # 次のサイクルまで待機
            sys_logger.info(
                f"次のサイクルまで {POLLING_INTERVAL_SECONDS}秒 待機中..."
            )
            for _ in range(POLLING_INTERVAL_SECONDS):
                if _shutdown_requested:
                    break
                await asyncio.sleep(1)

            if _shutdown_requested:
                sys_logger.info("シャットダウン要求により終了します。")
                break

    except Exception as e:
        sys_logger.error(f"予期しないエラー: {e}", exc_info=True)
    finally:
        await scraper.stop()
        sys_logger.info("プログラム終了")


if __name__ == "__main__":
    asyncio.run(main())
