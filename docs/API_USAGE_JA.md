# Qwen3-VL Embedding API 使用ガイド

OpenAI互換のマルチモーダル埋め込みAPIサーバーの使用方法を説明します。

## 目次

- [サーバーの起動](#サーバーの起動)
- [エンドポイント](#エンドポイント)
- [リクエスト形式](#リクエスト形式)
- [入力形式](#入力形式)
- [使用例](#使用例)
- [他の端末からの利用](#他の端末からの利用)

---

## サーバーの起動

### 基本的な起動

```bash
python api_server.py
```

### コマンドラインオプション

| オプション | 説明 | デフォルト値 |
|-----------|------|-------------|
| `--model-path` | モデルディレクトリのパス | `./models/Qwen3-VL-Embedding-2B` |
| `--host` | バインドするホスト | `0.0.0.0` |
| `--port` | バインドするポート | `8000` |
| `--log-level` | ログレベル (DEBUG/INFO/WARNING/ERROR) | `INFO` |

### 起動例

```bash
# カスタム設定で起動
python api_server.py --host 0.0.0.0 --port 9000 --model-path ./models/Qwen3-VL-Embedding-2B

# ヘルプを表示
python api_server.py --help
```

---

## エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/health` | GET | ヘルスチェック |
| `/v1/models` | GET | 利用可能なモデル一覧 |
| `/v1/embeddings` | POST | 埋め込みベクトルを生成 |

---

## リクエスト形式

### POST /v1/embeddings

```json
{
  "input": "テキストまたは画像",
  "model": "qwen3-vl-embedding",
  "encoding_format": "float",
  "dimensions": null,
  "user": null
}
```

### パラメータ説明

| パラメータ | 必須 | 型 | 説明 |
|-----------|:----:|-----|------|
| `input` | ✅ | string / array | 埋め込みを取得する入力データ |
| `model` | ❌ | string | モデル名（デフォルト: `qwen3-vl-embedding`） |
| `encoding_format` | ❌ | string | 出力形式（現在は`float`のみ対応） |
| `dimensions` | ❌ | int | 埋め込み次元数（未実装） |
| `user` | ❌ | string | ユーザー識別子（未実装） |

### レスポンス形式

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.123, -0.456, ...],
      "index": 0
    }
  ],
  "model": "qwen3-vl-embedding",
  "usage": {
    "prompt_tokens": 1,
    "total_tokens": 1
  }
}
```

---

## 入力形式

`input`パラメータは以下の形式をサポートしています：

### 1. テキスト（文字列）

```json
{
  "input": "犬と遊んでいる女性の画像を検索",
  "model": "qwen3-vl-embedding"
}
```

### 2. 画像URL

```json
{
  "input": "https://example.com/image.jpg",
  "model": "qwen3-vl-embedding"
}
```

### 3. サーバー側のローカルパス

```json
{
  "input": "./data/examples/0.jpeg",
  "model": "qwen3-vl-embedding"
}
```

### 4. Base64エンコード画像

```json
{
  "input": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "model": "qwen3-vl-embedding"
}
```

### 5. バッチ入力（配列）

```json
{
  "input": [
    "テキスト1",
    "テキスト2",
    "https://example.com/image.jpg"
  ],
  "model": "qwen3-vl-embedding"
}
```

### 6. 複合入力（テキスト + 画像 + instruction）

```json
{
  "input": [
    {
      "text": "この画像について説明してください",
      "image": "https://example.com/image.jpg",
      "instruction": "画像の内容を分析して関連テキストを取得"
    }
  ],
  "model": "qwen3-vl-embedding"
}
```

---

## 使用例

### Python

```python
import requests

API_URL = "http://localhost:8000/v1/embeddings"

# テキスト埋め込み
response = requests.post(API_URL, json={
    "input": "夕暮れのビーチで犬と遊ぶ女性",
    "model": "qwen3-vl-embedding"
})
result = response.json()
embedding = result["data"][0]["embedding"]
print(f"埋め込み次元数: {len(embedding)}")

# 画像URL埋め込み
response = requests.post(API_URL, json={
    "input": "https://example.com/photo.jpg",
    "model": "qwen3-vl-embedding"
})

# バッチ処理
response = requests.post(API_URL, json={
    "input": [
        "テキスト1",
        "テキスト2",
        "テキスト3"
    ],
    "model": "qwen3-vl-embedding"
})
embeddings = [d["embedding"] for d in response.json()["data"]]
```

### curl

```bash
# テキスト埋め込み
curl -X POST "http://localhost:8000/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, world!", "model": "qwen3-vl-embedding"}'

# 画像URL埋め込み
curl -X POST "http://localhost:8000/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d '{"input": "https://example.com/image.jpg", "model": "qwen3-vl-embedding"}'
```

---

## 他の端末からの利用

他の端末（クライアント）からAPIサーバーにローカル画像を送信する場合は、**Base64エンコード**を使用します。

### Python での送信

```python
import base64
import requests

API_URL = "http://サーバーIP:8000/v1/embeddings"

# 1. ローカル画像をBase64エンコード
with open("./my_local_image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# 2. Data URI形式で送信（推奨）
response = requests.post(API_URL, json={
    "input": f"data:image/jpeg;base64,{image_base64}",
    "model": "qwen3-vl-embedding"
})

# 3. テキストと画像の複合入力
response = requests.post(API_URL, json={
    "input": [
        {
            "text": "この画像の内容を説明してください",
            "image": f"data:image/jpeg;base64,{image_base64}",
            "instruction": "画像を分析"
        }
    ],
    "model": "qwen3-vl-embedding"
})

print(response.json())
```

### curl での送信

```bash
# 画像をBase64エンコードして送信
IMAGE_BASE64=$(base64 -i ./my_image.jpg)

curl -X POST "http://サーバーIP:8000/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"data:image/jpeg;base64,${IMAGE_BASE64}\", \"model\": \"qwen3-vl-embedding\"}"
```

### サポートされる画像形式

| 形式 | 説明 | 例 |
|------|------|-----|
| Data URI | MIMEタイプ付きBase64 | `data:image/jpeg;base64,/9j/4AAQ...` |
| 生Base64 | Base64文字列のみ | `/9j/4AAQSkZJRgABAQEASABI...` |
| URL | HTTP/HTTPS URL | `https://example.com/image.jpg` |
| サーバー側パス | APIサーバー上のパス | `./data/examples/0.jpeg` |

---

## 類似度計算の例

埋め込みベクトルを使用して、テキストと画像の類似度を計算できます。

```python
import requests
import numpy as np

API_URL = "http://localhost:8000/v1/embeddings"

# クエリとドキュメントの埋め込みを取得
response = requests.post(API_URL, json={
    "input": [
        {"text": "夕暮れのビーチで犬と遊ぶ女性", "instruction": "関連する画像を検索"},
        {"image": "https://example.com/beach_dog.jpg"},
        {"image": "https://example.com/city_night.jpg"}
    ],
    "model": "qwen3-vl-embedding"
})

data = response.json()["data"]
query_embedding = np.array(data[0]["embedding"])
doc1_embedding = np.array(data[1]["embedding"])
doc2_embedding = np.array(data[2]["embedding"])

# コサイン類似度を計算（正規化済みなので内積でOK）
similarity1 = np.dot(query_embedding, doc1_embedding)
similarity2 = np.dot(query_embedding, doc2_embedding)

print(f"画像1との類似度: {similarity1:.4f}")
print(f"画像2との類似度: {similarity2:.4f}")
```

---

## トラブルシューティング

### サーバーに接続できない

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

### モデルが見つからない

`--model-path`で正しいパスを指定してください：

```bash
python api_server.py --model-path /path/to/Qwen3-VL-Embedding-2B
```

### メモリ不足

バッチサイズを小さくするか、より小さいモデルを使用してください。
