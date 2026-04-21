"""
BTCC Tradfiスプレッド調査ツール - ログ設定
==========================================
3日間ローテーションのログ管理。
スプレッドデータはCSV風のフォーマットでファイルに記録し、
コンソールにも同時出力する。
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from config import LOG_DIR, LOG_FILENAME, LOG_BACKUP_COUNT


def setup_logger():
    """
    スプレッド記録用のロガーを設定する。
    
    ログ形式:
      2026-04-17 10:30:00 | XAUUSD | ゴールド | 4775.08 | 4774.90 | 0.18 | 0.0038%
    
    ファイル: logs/spreads.log（3日間保持、超過分は自動削除）
    コンソール: 同じ内容を標準出力にも表示
    """
    # ログディレクトリ作成
    os.makedirs(LOG_DIR, exist_ok=True)

    # メインロガー
    logger = logging.getLogger("btcc_spread")
    logger.setLevel(logging.INFO)

    # 既存のハンドラがあればクリア（再呼び出し防止）
    if logger.handlers:
        logger.handlers.clear()

    # ─── ファイルハンドラ: 日次ローテーション、3日分保持 ───
    log_path = os.path.join(LOG_DIR, LOG_FILENAME)
    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="D",              # 日次ローテーション
        interval=1,
        backupCount=LOG_BACKUP_COUNT,  # 3日分保持
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"  # バックアップファイル名の日付形式
    file_handler.setLevel(logging.INFO)

    # ─── コンソールハンドラ ───
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # ─── フォーマット（パイプ区切り、解析しやすい形式） ───
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def setup_system_logger():
    """
    システムログ用のロガーを設定する（エラー、ステータス情報など）。
    
    スプレッドデータとは別に、システムの動作状況を記録する。
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("btcc_system")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    # ─── ファイルハンドラ ───
    sys_log_path = os.path.join(LOG_DIR, "system.log")
    file_handler = TimedRotatingFileHandler(
        filename=sys_log_path,
        when="D",
        interval=1,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.DEBUG)

    # ─── コンソールハンドラ ───
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # ─── フォーマット ───
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
