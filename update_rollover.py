import json
import os
import logging
from datetime import datetime
from config import LOG_DIR

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_rollover_rates():
    """
    BTCCの翌日物金利（ロールオーバー手数料）を調査するスクリプト。
    現在はTradFi銘柄一律 0.02% を基準としている。
    """
    # 現時点でのBTCC Tradfi標準金利 (日次 0.02%)
    # カテゴリや銘柄ごとに変動があった場合に拡張可能な構造にする
    base_rate = 0.0002  # 0.02%
    
    # 銘柄カテゴリごとのデフォルト金利（拡張用）
    category_rates = {
        "stocks": 0.0002,
        "metals": 0.0002,
        "forex": 0.0002,
        "indices": 0.0002,
        "commodities": 0.0002
    }

    rollover_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "default_rate": base_rate,
        "category_rates": category_rates,
        "description": "BTCC TradFi Rollover Fee per day (0.02%)"
    }

    # 保存処理
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    output_path = os.path.join(LOG_DIR, "rollover_fees.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rollover_data, f, indent=4, ensure_ascii=False)
        logger.info(f"SUCCESS: 金利データを保存しました -> {output_path}")
    except Exception as e:
        logger.error(f"ERROR: 金利データの保存に失敗しました: {e}")

if __name__ == "__main__":
    fetch_rollover_rates()
