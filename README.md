# Image Cropper with GPT-4.1

このツールは、OpenAI の GPT-4.1モデルを活用して、**料理画像**から特定領域を自動でクロップする Python プログラムです。レシピの工程説明を入力するだけで、関連する部分を自動的に切り抜きます。

---

## 概要

料理画像から指定された工程に関連する領域を自動的に検出・クロップします。「にんじんを切ります」「肉を炒めます」といったレシピの指示文を入力するだけで、該当する調理シーンを自動的に識別し、16:9のアスペクト比で切り抜きます。

---

## 主な機能

- GPT-4.1を使用して画像解析を実施
- 入力したレシピ文の説明に基づいてクロップ領域を決定
- PIL と matplotlib による画像の視覚的表示
- クロップ結果を16:9のアスペクト比に自動調整
- クロップ結果と元画像を並べて確認可能
- 日本語説明文にも対応（matplotlib用フォント設定済み）

---

## セットアップ

### 必要要件

- Python環境
- OpenAI API Key

### 必要なライブラリ

以下のライブラリが必要です：

```bash
pip install openai Pillow matplotlib
```

### API Key の設定

環境変数にOpenAI API Keyを設定してください：

```bash
# Linux/macOS
export OPENAI_API_KEY='your-api-key-here'

# Windows (PowerShell)
$env:OPENAI_API_KEY='your-api-key-here'

# Windows (コマンドプロンプト)
set OPENAI_API_KEY=your-api-key-here
```

---

## 使い方

### 基本的な使用方法

```bash
python cropping.py --image path/to/image.jpg --instruction "タマネギを微塵切りにします。"
```

### オプション

| オプション | 説明 | デフォルト値 |
|-----------|------|------------|
| `--image` | 入力画像のパス（必須） | - |
| `--instruction` | クロップ領域の説明（必須） | - |
| `--output` | 出力ファイルのパス | タイムスタンプ付き自動生成 |
| `--output_dir` | 出力ディレクトリ | `output` |
| `--api_key` | OpenAI API Key | 環境変数から取得 |
| `--debug` | デバッグモード | オフ |

### 使用例

```bash
# 基本的な使用
python cropping.py --image kitchen.jpg --instruction "フライパンで炒めている野菜"

# 出力先を指定
python cropping.py --image food.jpg --instruction "皿に盛られた料理" --output result.jpg

# 出力ディレクトリを指定
python cropping.py --image cooking.jpg --instruction "ボウルで混ぜる" --output_dir ./results
```

---

## 出力例
- 入力画像に赤い枠でクロップ領域を表示
- 元画像（左）と16:9に調整された切り抜き画像（右）を並べて視覚的に表示
- クロップ領域の座標と GPT による簡易説明も表示
- デフォルトではoutputフォルダに切り出した画像を保存

---

## 技術詳細

### 処理フロー

1. 画像をBase64エンコード
2. GPT-4.1 APIに画像と指示文を送信
3. APIからクロップ座標（JSON形式）を取得
4. 座標を16:9比率に調整
5. 画像を切り出して保存
6. matplotlibで結果を表示

### 16:9比率調整アルゴリズム

- 元のクロップ領域を基準に、最小限の拡大で16:9に調整
- 画像の端に達した場合は自動的に調整
- 精密な浮動小数点計算により、高精度な比率調整を実現

### 日本語フォント対応について

matplotlibで日本語を正しく表示するために、OSごとに最適なフォントを自動選択する仕組みが含まれています。

- **Windows**: Yu Gothic, MS Gothic, Meiryo
- **macOS**: Hiragino Sans, Hiragino Maru Gothic ProN
- **Linux**: IPAGothic, Noto Sans CJK JP

---
