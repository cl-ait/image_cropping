# GPT-4 Vision Image Cropper

このツールは、OpenAI の GPT-4 Vision モデルを活用して、指定された画像内の特定領域を自動でクロップ（切り抜き）する Python プログラムです。指示文（プロンプト）を入力するだけで、対象物の座標を取得し、クロップ画像を生成・表示します。

---

## 仕様

- GPT-4o（GPT-4 Vision）を使用して画像解析を実施
- 指定した自然言語の説明に基づいてクロップ領域を自動算出
- PIL と matplotlib による画像の視覚的表示
- クロップ結果と元画像を並べて確認可能
- 日本語説明文にも対応（matplotlib用フォント設定済み）

---

## 必要なライブラリ

以下のライブラリが必要：

```bash
pip install openai Pillow matplotlib
```

## 使い方
```bash
python crop_with_gpt.py --image path/to/image.jpg --instruction "右上のリンゴ" --output cropped.jpg --api_key YOUR_API_KEY
```

| 引数            | 説明                                          |
|-----------------|-----------------------------------------------|
| `--image`       | クロップ対象の画像パス（必須）                      |
| `--instruction` | クロップ対象の自然言語による説明（必須）               |
| `--output`      | クロップ画像の出力先パス（任意、デフォルト: `cropped.jpg`） |
| `--api_key`     | OpenAI APIキー（環境変数でも指定可能）                |
| `--debug`       | APIレスポンスや座標などの詳細ログを出力               |

