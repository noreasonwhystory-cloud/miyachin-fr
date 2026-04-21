"""
BTCC Tradfiスプレッド調査ツール - 設定ファイル
================================================
全Tradfi銘柄の定義、ポーリング間隔、ログ設定を一元管理。
"""

import os
from datetime import timezone, timedelta

# ─────────────────────────────────────────────
# タイムゾーン
# ─────────────────────────────────────────────
JST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────
# BTCC取引ページのベースURL
# ─────────────────────────────────────────────
BTCC_BASE_URL = "https://www.btcc.com/en-US/trade/tradfi"

# ─────────────────────────────────────────────
# Tradfi全銘柄リスト（2026年4月調査時点）
# ─────────────────────────────────────────────
# 各銘柄のURL末尾に "USDT" が付加される
# 例: XAUUSD → /trade/tradfi/XAUUSDUSDT

TRADFI_SYMBOLS = {
    "metals": [
        {"symbol": "XAUUSD",  "name": "ゴールド",     "url_suffix": "XAUUSDUSDT"},
        {"symbol": "XAGUSD",  "name": "シルバー",     "url_suffix": "XAGUSDUSDT"},
        {"symbol": "XPTUSD",  "name": "プラチナ",     "url_suffix": "XPTUSDUSDT"},
        {"symbol": "XPDUSD",  "name": "パラジウム",   "url_suffix": "XPDUSDUSDT"},
        {"symbol": "XALUSD",  "name": "アルミニウム", "url_suffix": "XALUSDUSDT"},
        {"symbol": "COPPER",  "name": "銅",           "url_suffix": "COPPERUSDT"},
    ],
    "commodities": [
        {"symbol": "USOIL",   "name": "原油(WTI)",    "url_suffix": "USOILUSDT"},
        {"symbol": "UKOIL",   "name": "原油(ブレント)", "url_suffix": "UKOILUSDT"},
        {"symbol": "NGAS",    "name": "天然ガス",     "url_suffix": "NGASUSDT"},
    ],
    "indices": [
        {"symbol": "SP500",   "name": "S&P 500",      "url_suffix": "SP500USDT"},
        {"symbol": "TECH100", "name": "NASDAQ 100",   "url_suffix": "TECH100USDT"},
        {"symbol": "DJ30",    "name": "ダウ工業30",   "url_suffix": "DJ30USDT"},
        {"symbol": "GER30",   "name": "ドイツDAX",    "url_suffix": "GER30USDT"},
        {"symbol": "JPN225",  "name": "日経225",      "url_suffix": "JPN225USDT"},
        {"symbol": "UK100",   "name": "FTSE 100",     "url_suffix": "UK100USDT"},
    ],
    "forex": [
        {"symbol": "GBPUSD",  "name": "ポンド/ドル",  "url_suffix": "GBPUSDUSDT"},
        {"symbol": "EURUSD",  "name": "ユーロ/ドル",  "url_suffix": "EURUSDUSDT"},
        {"symbol": "AUDUSD",  "name": "豪ドル/ドル",  "url_suffix": "AUDUSDUSDT"},
        {"symbol": "NZDUSD",  "name": "NZドル/ドル",  "url_suffix": "NZDUSDUSDT"},
    ],
    "stocks": [
        {"symbol": "AAPL",    "name": "Apple",        "url_suffix": "AAPLUSDT"},
        {"symbol": "AMD",     "name": "AMD",          "url_suffix": "AMDUSDT"},
        {"symbol": "AMZN",    "name": "Amazon",       "url_suffix": "AMZNUSDT"},
        {"symbol": "COST",    "name": "Costco",       "url_suffix": "COSTUSDT"},
        {"symbol": "GOOG",    "name": "Alphabet",     "url_suffix": "GOOGUSDT"},
        {"symbol": "INTEL",   "name": "Intel",        "url_suffix": "INTELUSDT"},
        {"symbol": "META",    "name": "Meta",         "url_suffix": "METAUSDT"},
        {"symbol": "MSFT",    "name": "Microsoft",    "url_suffix": "MSFTUSDT"},
        {"symbol": "MSTR",    "name": "MicroStrategy","url_suffix": "MSTRUSDT"},
        {"symbol": "NFLX",    "name": "Netflix",      "url_suffix": "NFLXUSDT"},
        {"symbol": "NVIDIA",  "name": "NVIDIA",       "url_suffix": "NVIDIAUSDT"},
        {"symbol": "ORCL",    "name": "Oracle",       "url_suffix": "ORCLUSDT"},
        {"symbol": "PLTR",    "name": "Palantir",     "url_suffix": "PLTRUSDT"},
        {"symbol": "TSLA",    "name": "Tesla",        "url_suffix": "TSLAUSDT"},
        {"symbol": "TSM",     "name": "TSMC",         "url_suffix": "TSMUSDT"},
    ],
}


def get_all_symbols():
    """全Tradfi銘柄をフラットなリストとして取得する"""
    symbols = []
    for category, items in TRADFI_SYMBOLS.items():
        for item in items:
            symbols.append({**item, "category": category})
    return symbols


# ─────────────────────────────────────────────
# ポーリング設定
# ─────────────────────────────────────────────
# 全銘柄の巡回完了後、次サイクルまでの待機時間（秒）
POLLING_INTERVAL_SECONDS = int(os.environ.get("BTCC_POLLING_INTERVAL", "300"))  # デフォルト5分

# 1銘柄あたりの最大待機時間（秒）
PAGE_LOAD_TIMEOUT_SECONDS = 15

# エラー時のリトライ回数
MAX_RETRIES = 3

# リトライ時の初期待機時間（秒）。指数バックオフで増加。
RETRY_BACKOFF_BASE = 2

# ─────────────────────────────────────────────
# ログ設定
# ─────────────────────────────────────────────
LOG_DIR = os.environ.get("BTCC_LOG_DIR", os.path.join(os.path.dirname(__file__), "logs"))
LOG_FILENAME = "spreads.log"
LOG_BACKUP_COUNT = 3  # 3日分保持

# ─────────────────────────────────────────────
# ブラウザ設定
# ─────────────────────────────────────────────
HEADLESS = os.environ.get("BTCC_HEADLESS", "true").lower() == "true"
