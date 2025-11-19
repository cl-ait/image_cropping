import os
import datetime
import base64
from PIL import Image, ImageDraw
import json
from openai import OpenAI
import argparse
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager
import sys

# 日本語フォント太陽
def japanese_fonts():
    """matplotlibで日本語フォントを使用するための設定"""
    # プラットフォームに応じたフォント設定
    if sys.platform.startswith('win'):  # Windows
        font_dirs = ['C:/Windows/Fonts']
        font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
        
        # 利用可能なフォントをチェック
        available_fonts = [f.name for f in font_manager.fontManager.ttflist]
        print("利用可能なフォント:", available_fonts[:5], "...")
        
        # MS Gothic, Yu Gothic, Meiryo などを優先的に使用
        for font_name in ['Yu Gothic', 'MS Gothic', 'Meiryo', 'Yu Mincho', 'MS Mincho']:
            if any(font_name.lower() in font.lower() for font in available_fonts):
                plt.rcParams['font.family'] = font_name
                print(f"フォント '{font_name}' を使用します")
                return
                
    elif sys.platform.startswith('darwin'):  # macOS
        # macOSの日本語フォント
        for font_name in ['Hiragino Sans', 'Hiragino Maru Gothic ProN', 'Osaka', 'AppleGothic']:
            try:
                matplotlib.rc('font', family=font_name)
                print(f"フォント '{font_name}' を使用します")
                return
            except:
                continue
                
    elif sys.platform.startswith('linux'):  # Linux
        # IPAフォントなどがインストールされていることを前提
        for font_name in ['IPAGothic', 'IPAPGothic', 'Noto Sans CJK JP']:
            try:
                matplotlib.rc('font', family=font_name)
                print(f"フォント '{font_name}' を使用します")
                return
            except:
                continue
    
    # デフォルトのフォールバック設定
    try:
        # 一般的なフォールバック: sans-serif
        matplotlib.rc('font', family='sans-serif')
        # matplotlibのデフォルトフォントリストに日本語対応フォントを追加
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans GB', 'Microsoft YaHei', 'sans-serif']
        print("デフォルトのsans-serifフォントを使用します")
    except:
        print("フォントの設定に失敗しました。")

def generate_output_filename(output_dir, base_name="cropped", extension="jpg"):
    """タイムスタンプ付きのファイル名を生成する"""
    # 現在の日時を取得
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # ファイル名を生成
    filename = f"{base_name}_{timestamp}.{extension}"
    # return filename
    # フルパスを返す
    return os.path.join(output_dir, filename)

def encode_image_to_base64(image_path):
    """画像をbase64エンコードする"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def crop_image_with_gpt(image_path, instruction):
    """GPT-4 Vision APIを使用して画像からクロップ領域の座標を取得"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("環境変数 OPENAI_API_KEY が設定されていません。")
    client = OpenAI(api_key=api_key)
    
    # 画像サイズを取得
    with Image.open(image_path) as img:
        img_width, img_height = img.size
    
    # 画像をbase64エンコード
    base64_image = encode_image_to_base64(image_path)
    
    # システムプロンプトとユーザープロンプトを準備
    system_prompt = f"""
    あなたは料理画像解析の専門家です。
    ユーザーから送られてきた料理画像に対して、レシピ指示に関連する部分をクロッピングするための座標を提供してください。

    具体例:
    - 「にんじんを切ります」→ 画像内で切られている、または切る準備ができているにんじんや包丁、まな板などの調理器具が収まるように探す
    - 「肉を炒めます」→ フライパンで炒められている肉や、これから炒める予定の肉を探す
    - 「ボウルで混ぜます」→ 材料が入ったボウルを探す
    - 「油を引きます」や「フライパンに油をひきます」→ 油を注いでいる手元、油の容器、フライパンの表面、あるいはその直前の準備動作が見られる場所を探す
    - 「醤油を入れます」→ 醤油の容器やフライパン、鍋を探す

    指示に従う際のガイドライン：
    1. 食材や調味料、または「手の動作」が画像の中央付近に来るような範囲を優先してクロップしてください。
    2. 調理器具は、現在使用されている・もしくは使用直前であるもののみを含めてください。
    3. 関連する食材と関係のない調理器具は可能な限り含めないでください。
    4. 動作が抽象的で画像から明確でない場合（例：「油を引く」）は、動作に使われる道具（油のボトル、フライパン）と、手が関与していそうな部分を優先してクロップしてください。
    5. 明確な調理シーンが存在しない場合は、レシピ指示に最も関係する道具や食材を中央に配置した状態でクロップ範囲を決定してください。
    6. どうしても複数の候補がある場合は、最も関連性が高く、かつ視覚的に分かりやすい部分を優先してください。

    
    画像のサイズは幅{img_width}ピクセル、高さ{img_height}ピクセルです。
    このサイズ内で有効な座標を返してください。
    
    あなたの出力は必ず以下のJSON形式に厳密に従ってください：
    
    {{
        "crop_coordinates": {{
            "x_min": 整数値,
            "y_min": 整数値,
            "x_max": 整数値,
            "y_max": 整数値
        }},
        "description": "このクロップ画像はどんな料理道具を用いてどのような料理工程を行なっているか一言で書いてください。"
    }}
    
    説明と注意点:
    - x_min, y_min は左上の座標、x_max, y_max は右下の座標です
    - 座標は元の画像のピクセル単位で整数値で指定してください
    - 必ず有効な座標を返してください (x_min < x_max かつ y_min < y_max)
    - 必ず画像範囲内の座標を指定してください (0 <= x_min < x_max <= {img_width} かつ 0 <= y_min < y_max <= {img_height})
    - JSONフォーマット以外のテキストや説明は一切含めないでください
    - 必ず有効なJSONを出力してください
    - コードブロック記号(```)は含めないでください
    """
    
    user_prompt =f"この料理画像から「{instruction}」に関連する部分をクロッピングするための座標を教えてください。レシピ指示に関係する食材や調味料または手元を画像の中央付近に含めるようにクロップ範囲を選んでください。"
    
    # API呼び出し
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=1000
    )
    
    # レスポンスからJSON部分を抽出
    response_text = response.choices[0].message.content
    print("APIからのレスポンス（デバッグ用）:")
    print(response_text)
    
    # JSONの抽出を改善
    if '```json' in response_text:
        json_start = response_text.find('```json') + 7
        json_end = response_text.find('```', json_start)
        json_str = response_text[json_start:json_end].strip()
    else:
        # 単純に最初の{から最後の}までを抽出
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end].strip()
        else:
            print("JSONが見つかりませんでした")
            return None
    
    print("抽出されたJSON文字列:")
    print(json_str)
    
    try:
        # JSONパース
        result = json.loads(json_str)
        
        # 座標が画像サイズの範囲内かチェック
        coords = result['crop_coordinates']
        if coords['x_min'] < 0 or coords['y_min'] < 0 or coords['x_max'] > img_width or coords['y_max'] > img_height:
            print("警告: 座標が画像の範囲外です。座標を調整します。")
            coords['x_min'] = max(0, min(coords['x_min'], img_width - 1))
            coords['y_min'] = max(0, min(coords['y_min'], img_height - 1))
            coords['x_max'] = max(coords['x_min'] + 1, min(coords['x_max'], img_width))
            coords['y_max'] = max(coords['y_min'] + 1, min(coords['y_max'], img_height))
            print(f"調整後の座標: ({coords['x_min']}, {coords['y_min']}) to ({coords['x_max']}, {coords['y_max']})")
        
        return result
    except json.JSONDecodeError as e:
        print(f"JSONのパースに失敗しました: {e}")
        # JSONをより寛容にパースする追加の試み
        try:
            # 引用符の修正を試みる
            fixed_json = json_str.replace("'", '"')
            result = json.loads(fixed_json)
            return result
        except:
            print("修正を試みましたが失敗しました。APIのレスポンス全体:")
            print(response_text)
            return None

def crop_and_save_image(image_path, crop_coordinates, output_path, force_16_9_ratio=True):
    """画像をクロップして保存。16:9の比率にする"""
    with Image.open(image_path) as img:
        # 画像サイズを取得
        img_width, img_height = img.size
        print(f"元画像サイズ: {img_width}x{img_height}")
        
        # クロップ座標を取得し、画像の範囲内に収める
        x_min = max(0, int(crop_coordinates["x_min"]))
        y_min = max(0, int(crop_coordinates["y_min"]))
        x_max = min(img_width, int(crop_coordinates["x_max"]))
        y_max = min(img_height, int(crop_coordinates["y_max"]))
        
        print(f"初期クロップ座標: ({x_min}, {y_min}) to ({x_max}, {y_max})")
        
        # 有効な座標かチェック
        if x_min >= x_max or y_min >= y_max:
            print("エラー: 無効なクロップ座標です。最小値の座標を調整します。")
            # 最小サイズのクロップ領域を作成
            if x_min >= x_max:
                x_max = min(x_min + 10, img_width)
            if y_min >= y_max:
                y_max = min(y_min + 10, img_height)
            print(f"調整後の座標: ({x_min}, {y_min}) to ({x_max}, {y_max})")
        
        # 16:9の比率に調整
        if force_16_9_ratio:
            # 16:9比率調整前の座標を保存（表示用）
            original_coords = {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max
            }
            
            # 16:9の比率に精密に調整（新しい関数を使用）
            adjusted_coords = adjust_crop_to_exact_16_9_ratio(
                {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
                img_width, img_height
            )
            
            x_min = adjusted_coords["x_min"]
            y_min = adjusted_coords["y_min"]
            x_max = adjusted_coords["x_max"]
            y_max = adjusted_coords["y_max"]
            
            # 調整前後の座標を比較
            print(f"16:9比率に調整前: 幅={original_coords['x_max']-original_coords['x_min']}, 高さ={original_coords['y_max']-original_coords['y_min']}")
            print(f"16:9比率に調整後: 幅={x_max-x_min}, 高さ={y_max-y_min}")
            print(f"比率: {(x_max-x_min)/(y_max-y_min):.6f} (目標: 1.777778)")
            
        print(f"最終クロップ座標: ({x_min}, {y_min}) to ({x_max}, {y_max})")
            
        # クロップ
        try:
            cropped_img = img.crop((x_min, y_min, x_max, y_max))
            cropped_img.save(output_path)
            print(f"クロップした画像サイズ: {cropped_img.width}x{cropped_img.height}")
            return cropped_img, {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max}
        except Exception as e:
            print(f"画像のクロップ中にエラーが発生しました: {e}")
            return None, None

def adjust_crop_to_exact_16_9_ratio(crop_coordinates, img_width, img_height):
    """クロップ座標を正確に16:9の比率に調整する関数（拡大優先・精密計算）"""
    x_min = crop_coordinates["x_min"]
    y_min = crop_coordinates["y_min"]
    x_max = crop_coordinates["x_max"]
    y_max = crop_coordinates["y_max"]
    
    # 現在のクロップ領域の幅と高さを計算
    current_width = x_max - x_min
    current_height = y_max - y_min
    
    # 目標とする比率
    target_ratio = 16/9 
    
    # 現在の比率を計算
    current_ratio = current_width / current_height if current_height != 0 else 0
    
    print(f"現在の比率: {current_ratio:.4f} (目標: {target_ratio:.4f})")
    print(f"調整前: 幅={current_width}, 高さ={current_height}")
    
    # 精密な計算のため浮動小数点で計算
    if current_ratio <= target_ratio:
        # 幅を増やす（高さを固定）
        new_width = int(current_height * target_ratio + 0.5)  # 四捨五入
        width_diff = new_width - current_width
        
        # 左右均等に拡張
        new_x_min = max(0, x_min - width_diff // 2)
        new_x_max = min(img_width, new_x_min + new_width)
        
        # 画像の端に達した場合の調整
        if new_x_max > img_width:
            new_x_max = img_width
            new_x_min = max(0, new_x_max - new_width)
        
        # 高さはそのまま
        new_y_min = y_min
        new_y_max = y_max
        
    else:
        # 高さを増やす（幅を固定）
        new_height = int(current_width / target_ratio + 0.5)  # 四捨五入
        height_diff = new_height - current_height
        
        # 上下均等に拡張
        new_y_min = max(0, y_min - height_diff // 2)
        new_y_max = min(img_height, new_y_min + new_height)
        
        # 画像の端に達した場合の調整
        if new_y_max > img_height:
            new_y_max = img_height
            new_y_min = max(0, new_y_max - new_height)
        
        # 幅はそのまま
        new_x_min = x_min
        new_x_max = x_max
    
    # 最終確認：範囲内に収まっているか
    new_x_min = max(0, int(new_x_min))
    new_y_min = max(0, int(new_y_min))
    new_x_max = min(img_width, int(new_x_max))
    new_y_max = min(img_height, int(new_y_max))
    
    # この時点での比率を確認
    final_width = new_x_max - new_x_min
    final_height = new_y_max - new_y_min
    final_ratio = final_width / final_height if final_height != 0 else 0
    
    print(f"一次調整後: 幅={final_width}, 高さ={final_height}")
    print(f"一次調整後の比率: {final_ratio:.4f}")
    
    # 比率の誤差が大きい場合は、ピクセル単位で微調整
    if abs(final_ratio - target_ratio) > 0.0001:
        if final_ratio < target_ratio:
            # 幅を1ピクセルずつ増やす
            while (new_x_max - new_x_min) / (new_y_max - new_y_min) < target_ratio and new_x_max < img_width:
                new_x_max += 1
            # それでも足りない場合は幅を減らす
            while (new_x_max - new_x_min) / (new_y_max - new_y_min) < target_ratio and new_y_max > new_y_min + 1:
                new_y_max -= 1
        else:
            # 高さを1ピクセルずつ増やす
            while (new_x_max - new_x_min) / (new_y_max - new_y_min) > target_ratio and new_y_max < img_height:
                new_y_max += 1
            # それでも足りない場合は幅を減らす
            while (new_x_max - new_x_min) / (new_y_max - new_y_min) > target_ratio and new_x_max > new_x_min + 1:
                new_x_max -= 1
    
    # 最終的な比率を計算
    final_width = new_x_max - new_x_min
    final_height = new_y_max - new_y_min
    final_ratio = final_width / final_height if final_height != 0 else 0
    
    # 浮動小数点の計算誤差を考慮して、目標比率との絶対誤差を計算
    ratio_error = abs(final_ratio - target_ratio)
    
    print(f"最終調整後: 幅={final_width}, 高さ={final_height}")
    print(f"最終比率: {final_ratio:.6f} (目標: {target_ratio:.6f}, 誤差: {ratio_error:.6f})")
    
    # 元のクロップ領域との比較
    original_width = x_max - x_min
    original_height = y_max - y_min
    width_change = final_width - original_width
    height_change = final_height - original_height
    print(f"元領域からの変化: 幅 {width_change:+d}px ({(width_change/original_width*100):+.1f}%), 高さ {height_change:+d}px ({(height_change/original_height*100):+.1f}%)")
    
    return {
        "x_min": new_x_min,
        "y_min": new_y_min,
        "x_max": new_x_max,
        "y_max": new_y_max
    }

def display_results(original_image_path, cropped_image_path, crop_coordinates, description):
    """元画像とクロップした画像を表示し、座標情報を描画"""
    try:
        # 元画像を読み込み
        original_img = Image.open(original_image_path)
        original_draw = ImageDraw.Draw(original_img)
        
        # クロップした領域を矩形で表示
        x_min = int(crop_coordinates["x_min"])
        y_min = int(crop_coordinates["y_min"])
        x_max = int(crop_coordinates["x_max"])
        y_max = int(crop_coordinates["y_max"])
        
        # 赤い矩形を描画
        original_draw.rectangle([(x_min, y_min), (x_max, y_max)], outline="red", width=3)
        
        # クロップした画像ファイルがあるか確認
        if not os.path.exists(cropped_image_path):
            print(f"警告: クロップ画像ファイル {cropped_image_path} が見つかりません")
            return
            
        # クロップした画像を読み込み
        cropped_img = Image.open(cropped_image_path)
        if cropped_img.size == (0, 0):
            print("警告: クロップされた画像のサイズが0です")
            return
            
        # 図を作成
        fig, axes = plt.subplots(1, 2, figsize=(15, 8))
        
        # 元画像を表示
        axes[0].imshow(original_img)
        axes[0].set_title("Original Image with Crop Region")
        axes[0].axis('off')
        
        # クロップした画像を表示
        axes[1].imshow(cropped_img)
        # 説明文はASCII文字のみにフォールバック
        safe_description = description
        try:
            # 日本語を含む説明文を表示
            axes[1].set_title(f"Cropped Image\n{description}", fontsize=12)
        except:
            # 文字化けする場合はASCII文字のみに
            safe_description = ''.join([c if ord(c) < 128 else '?' for c in description])
            axes[1].set_title(f"Cropped Image\n{safe_description}", fontsize=12)
        axes[1].axis('off')
        
        # 座標情報を表示
        coordinate_text = f"Coordinates: ({x_min}, {y_min}) to ({x_max}, {y_max})"
        plt.figtext(0.5, 0.01, coordinate_text, ha="center", fontsize=12, bbox={"facecolor":"white", "alpha":0.5, "pad":5})
        
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"結果表示中にエラーが発生しました: {e}")
        print("クロップ座標:", crop_coordinates)

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='GPT-4 Visionを使用して画像をクロッピング')
    parser.add_argument('--image', required=True, help='クロッピングする画像のパス')
    parser.add_argument('--instruction', required=True, help='クロッピングする部分の説明（例: "猫の顔"）')
    parser.add_argument('--output', default=None, help='出力画像のパス（指定しない場合は自動でタイムスタンプ付きファイル名を生成）')
    # コマンドライン引数の設定に以下を追加
    parser.add_argument('--output_dir', default='output', help='出力ディレクトリのパス（デフォルト: output）')
    parser.add_argument('--api_key', help='OpenAI APIキー（環境変数OPENAI_API_KEYでも設定可能）')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効化')
    
    args = parser.parse_args()
    
    # 日本語フォントのセットアップ
    japanese_fonts()
    
    # APIキーの取得
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("APIキーが必要です。--api_keyオプションか環境変数OPENAI_API_KEYで指定してください。")
    
    # 入力画像が存在することを確認
    if not os.path.exists(args.image):
        print(f"エラー: 指定された画像ファイル '{args.image}' が見つかりません。")
        return
        
    try:
        # 入力画像を開いてテスト
        with Image.open(args.image) as test_img:
            img_width, img_height = test_img.size
            print(f"入力画像の読み込みに成功しました。サイズ: {img_width}x{img_height}")
    except Exception as e:
        print(f"エラー: 画像ファイルの読み込みに失敗しました: {e}")
        return
    
    # GPT-4 Visionでクロップ座標を取得
    print(f"画像の分析中: {args.image}")
    print(f"指示: {args.instruction}")
    
    try:
        result = crop_image_with_gpt(args.image, args.instruction)
    except Exception as e:
        print(f"GPT-4 Vision API呼び出し中にエラーが発生しました: {e}")
        return
    
    if not result:
        print("クロップ座標の取得に失敗しました。")
        return
    
    # 結果が期待通りのフォーマットか確認
    if 'crop_coordinates' not in result:
        print("エラー: APIレスポンスに 'crop_coordinates' が含まれていません。")
        print("受信したデータ:", result)
        return
        
    required_keys = ['x_min', 'y_min', 'x_max', 'y_max']
    if not all(key in result['crop_coordinates'] for key in required_keys):
        print("エラー: クロップ座標データが不完全です。")
        print("受信したデータ:", result['crop_coordinates'])
        return
    
    # 説明フィールドの確認
    description = result.get('description', '説明なし')
    
    # 座標情報を表示
    print("クロップ座標:")
    print(f"左上: ({result['crop_coordinates']['x_min']}, {result['crop_coordinates']['y_min']})")
    print(f"右下: ({result['crop_coordinates']['x_max']}, {result['crop_coordinates']['y_max']})")
    print(f"説明: {description}")

    if args.output:
        output_filename = args.output
    else:
        # 自動でタイムスタンプ付きファイル名を生成（指定されたディレクトリに）
        output_filename = generate_output_filename(output_dir=args.output_dir)
    
    # 画像をクロップして保存
    cropped_img = crop_and_save_image(args.image, result['crop_coordinates'], output_filename)
    
    if cropped_img:
        print(f"クロップした画像を保存しました: {output_filename}")
        
        # 結果を表示
        display_results(args.image, output_filename, result['crop_coordinates'], description)
    else:
        print("クロッピング処理に失敗しました。")

if __name__ == "__main__":
    main()

