# 📊 BTCC Tradfiスプレッド調査ツール

BTCC取引所のTradFi（伝統的金融）銘柄の内部スプレッド（Bid/Ask差）を定期的に監視し、ログに記録するツールです。

## 対象銘柄（全41銘柄）

| カテゴリ | 銘柄数 | 例 |
|---------|--------|-----|
| 貴金属 | 6 | XAUUSD, XAGUSD, COPPER |
| エネルギー | 3 | USOIL, UKOIL, NGAS |
| 株価指数 | 6 | SP500, TECH100, DJ30 |
| 外国為替 | 4 | GBPUSD, EURUSD |
| 個別株式 | 16 | AAPL, TSLA, NVIDIA |

> ⚠️ 仮想通貨（BTC, ETH等）は対象外です。

## セットアップ

### 1. 必要条件
- Python 3.10以上

### 2. インストール
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. 実行
```bash
# 1回だけ実行（テスト）
python main.py --once

# 連続実行（本番）
python main.py
```

### 4. Docker実行
```bash
docker build -t btcc-spread .
docker run -v ./logs:/app/logs btcc-spread
```

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `BTCC_POLLING_INTERVAL` | `300` | ポーリング間隔（秒） |
| `BTCC_LOG_DIR` | `./logs` | ログ出力先 |
| `BTCC_HEADLESS` | `true` | ヘッドレスモード |

## ログ形式

```
2026-04-17 10:30:00 | XAUUSD     | ゴールド      | Bid:      4774.90 | Ask:      4775.08 | Spread:       0.18 |  0.0038%
```

- `spreads.log` : スプレッドデータ（3日間保持、日次ローテーション）
- `system.log` : システムログ（エラー、ステータス）

## 技術スタック

- **Python** + **Playwright**（ヘッドレスブラウザ）
- REST APIが非公開のため、Webスクレイピングでデータ取得
- クラウド展開対応（Docker）
