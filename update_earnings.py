import json
import os
import yfinance as yf
from datetime import datetime
import logging
from config import TRADFI_SYMBOLS, LOG_DIR

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ticker名のマッピング (BTCC -> Yahoo Finance)
TICKER_MAPPING = {
    "INTEL": "INTC",
    "NVIDIA": "NVDA",
    "GOOG": "GOOGL",
}

def fetch_earnings_dates():
    """config.pyの銘柄リストから米国株の決算日を取得し保存する"""
    stocks = TRADFI_SYMBOLS.get("stocks", [])
    earnings_map = {}
    
    logger.info(f"Checking earnings for {len(stocks)} stocks...")
    
    for item in stocks:
        btcc_symbol = item["symbol"]
        # マッピングがあれば変換、なければそのまま
        yf_symbol = TICKER_MAPPING.get(btcc_symbol, btcc_symbol)
        
        try:
            # Ticker オブジェクト作成
            ticker = yf.Ticker(yf_symbol)
            calendar = ticker.calendar
            
            # yfinanceのcalendar形式のパース
            if calendar and 'Earnings Date' in calendar:
                dates = calendar['Earnings Date']
                if dates:
                    # 最も近い決算日を文字列(YYYY-MM-DD)として保存
                    earnings_date = dates[0].strftime('%Y-%m-%d')
                    earnings_map[btcc_symbol] = earnings_date
                    logger.info(f"SUCCESS: {btcc_symbol} (YF:{yf_symbol}) -> {earnings_date}")
                else:
                    logger.warning(f"NO DATE: {btcc_symbol} (Calendar found but no dates)")
            else:
                logger.warning(f"NO CALENDAR: {btcc_symbol}")
                
        except Exception as e:
            logger.error(f"ERROR: {btcc_symbol} 取得失敗: {e}")

    # 保存処理
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    output_path = os.path.join(LOG_DIR, "earnings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": earnings_map
        }, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Saved {len(earnings_map)} earnings dates to {output_path}")

if __name__ == "__main__":
    fetch_earnings_dates()
