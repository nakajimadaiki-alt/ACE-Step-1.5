# video_editor

React + Vite で作ったシンプルな動画編集UIです。

## 機能

- シーン切り替え（静止画 / 再現テンプレ / 自動演出 / モーショングラフィックス / 円盤回転）
- タイムラインで再生・停止・シーク
- 静止画を固定表示し続ける
- 円盤回転シーン（シンプル / レコード盤スタイル）
- 画像位置調整（X/Y オフセット + ズーム）
- UIからのMP4エクスポート（プログレスバー付き）
- CLIエクスポート（連番レンダリング + ffmpeg結合）
- ループ出力対応（短いクリップを指定秒数まで繰り返し）

## 1. セットアップ

### 必須

- Node.js (推奨: LTS)
- npm

### エクスポート時に追加で必須

- ffmpeg（PATHに通す）
- Playwright

```bash
npm install
npm i -D playwright
npx playwright install chromium
```

## 2. 開発サーバー起動

```bash
npm run dev
```

起動後、表示されたURL（通常 `http://localhost:5173`）を開きます。

## 3. シーンの使い方

### 静止画表示

1. 左メニューで `静止画表示` を選択
2. `ファイル選択` で画像を選ぶ（推奨）
3. 再生しても同じ画像が表示され続けます

入力欄に `public` 配下パスや画像URLを直接指定することもできます。
例: `public/my-image.jpg` を置いた場合 → `/my-image.jpg`

### 円盤回転

1. 左メニューで `円盤回転` を選択
2. 画像をアップロード（サーバーに保存され、エクスポート時もそのまま使えます）
3. `シンプル` or `レコード盤` スタイルを切り替え
4. **X位置 / Y位置 / ズーム** スライダーで画像の表示位置を調整
5. 再生すると画像が回転します

### 自動演出モード

1. 左メニューで `自動演出モード` を選択
2. 台本入力欄にテキストを追加（Enter or 追加ボタン）
3. 各テキストにランダムなエフェクト（fade/slide/bounce）が付きます

## 4. UIからMP4エクスポート

円盤回転シーンでは、サイドバーのエクスポートパネルから直接MP4を書き出せます。

1. 画像をアップロードし、位置・ズームを調整
2. **再生時間**スライダーで出力秒数を設定（1〜60秒）
3. 必要に応じて**ループ**スライダーで合計秒数を指定（0＝ループなし）
4. **MP4エクスポート**ボタンをクリック
5. プログレスバーで進捗を確認
6. 完了後、**ダウンロード**ボタンでMP4を取得

## 5. CLIエクスポート

コマンドラインからもエクスポートできます。

### 基本コマンド

```bash
# 静止画シーン（public/my-image.jpg を使用、10秒）
npm run export -- --scene static --image /my-image.jpg --duration 10 --fps 30 --out ./dist/static.mp4

# 再現テンプレート（8秒）
npm run export -- --scene recreation --duration 8 --fps 30 --out ./dist/recreation.mp4

# 自動演出（6秒）
npm run export -- --scene auto --duration 6 --fps 30 --out ./dist/auto.mp4

# モーショングラフィックス（6秒）
npm run export -- --scene example --duration 6 --fps 30 --out ./dist/example.mp4

# 円盤回転 - シンプル（10秒）
npm run export -- --scene disc --image /my-image.jpg --duration 10 --fps 30 --out ./dist/disc.mp4

# 円盤回転 - レコード盤スタイル + 位置調整（10秒）
npm run export -- --scene disc --image /my-image.jpg --disc-style vinyl --image-offset-x 30 --image-offset-y 20 --image-scale 1.5 --duration 10 --fps 30 --out ./dist/disc-vinyl.mp4
```

### ループ出力（長時間動画）

短いクリップをループして長い動画を作成できます。例えば25秒の円盤回転を1時間ループ:

```bash
npm run export -- --scene disc --image /my-image.jpg --disc-style vinyl --duration 25 --fps 30 --loop-duration 3600 --out ./dist/disc-1h.mp4
```

### 既存の開発サーバーを使う

`--base-url` を指定すると、新しいViteサーバーを起動せず既存のサーバーを利用します。UIエクスポートで内部的に使われる仕組みです。

```bash
npm run export -- --scene disc --image /uploads/xxx.png --base-url http://127.0.0.1:5173 --duration 10 --out ./dist/disc.mp4
```

### 全オプション一覧

| オプション | 説明 | デフォルト |
|---|---|---|
| `--scene` | `static` / `recreation` / `auto` / `example` / `disc` | `static` |
| `--image` | 静止画・円盤シーンの画像パス | (なし) |
| `--disc-style` | 円盤スタイル: `simple` / `vinyl` | `simple` |
| `--image-offset-x` | 画像X位置 (0-100%) | `50` |
| `--image-offset-y` | 画像Y位置 (0-100%) | `50` |
| `--image-scale` | 画像ズーム (1.0-3.0) | `1` |
| `--duration` | 秒数 | `5` |
| `--fps` | フレームレート | `30` |
| `--width` | 出力幅 (px) | `1920` |
| `--height` | 出力高 (px) | `1080` |
| `--out` | 出力先MP4パス | `./dist/export.mp4` |
| `--port` | レンダー用サーバーポート | `4173` |
| `--base-url` | 既存サーバーURL（指定時はVite起動をスキップ） | (なし) |
| `--loop-duration` | ループ後の合計秒数（0=ループなし） | `0` |

## 6. 品質チェック

```bash
npm run lint
```

## 7. よくあるエラー

| エラー | 対処 |
|---|---|
| `ffmpeg is not installed or not in PATH.` | ffmpegをインストールしPATHに通す |
| `Missing dependency: playwright` | `npm i -D playwright && npx playwright install chromium` |
| 画像が表示されない | ファイル選択で画像をアップロードするか、`public/` に画像を置いてパスを指定 |
| エクスポートが進まない | ffmpegとPlaywright（Chromium）がインストール済みか確認 |
