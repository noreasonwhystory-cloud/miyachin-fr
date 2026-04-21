FROM python:3.12-slim

# システム依存関係（Playwright用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium

# アプリケーションコピー
COPY *.py .

# ログディレクトリ
RUN mkdir -p /app/logs
VOLUME /app/logs

# 環境変数
ENV BTCC_HEADLESS=true
ENV BTCC_LOG_DIR=/app/logs
ENV BTCC_POLLING_INTERVAL=300

CMD ["python", "main.py"]
