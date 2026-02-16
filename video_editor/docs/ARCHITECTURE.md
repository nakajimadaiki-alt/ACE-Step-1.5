# Video Editor - アーキテクチャ & 機能一覧

## 技術スタック

| 区分 | 技術 |
|------|------|
| フロントエンド | React 19 + Vite (rolldown-vite) |
| バックエンド | Vite Dev Server カスタムミドルウェア (Node.js) |
| エクスポート | Playwright (ブラウザキャプチャ) + ffmpeg (エンコード) |
| 言語 | JavaScript (JSX) |

---

## プロジェクト構成

```
video_editor/
├── index.html                 # エントリポイント HTML
├── vite.config.js             # Vite設定 + バックエンドAPIプラグイン
├── package.json
├── scripts/
│   └── export-video.mjs       # MP4エクスポートスクリプト (CLI/サーバー連携)
├── public/
│   └── uploads/               # アップロード画像保存先
├── src/
│   ├── main.jsx               # ReactDOM マウント
│   ├── App.jsx                # ルーティング (/ → Editor, /export → ExportRenderer)
│   ├── constants.js           # 定数 (FPS=30, デフォルト再生時間 等)
│   ├── hooks/
│   │   └── useVideoEngine.js  # 再生エンジン (フレーム管理・再生/停止/シーク)
│   ├── components/
│   │   ├── Editor.jsx         # メインエディタ (サイドバー + プレビュー統合)
│   │   ├── Preview.jsx        # プレビュー表示枠
│   │   ├── Timeline.jsx       # タイムライン (フレームルーラー + 再生ヘッド)
│   │   ├── Sidebar.jsx        # (未使用のアセットリスト雛形)
│   │   ├── StaticImageScene.jsx   # 静止画シーン
│   │   ├── RecreationScene.jsx    # 動画再現テンプレートシーン
│   │   ├── AutoScene.jsx          # 自動演出モードシーン
│   │   ├── ExampleScene.jsx       # モーショングラフィックスシーン
│   │   ├── DiscScene.jsx          # 円盤回転シーン
│   │   └── ExportRenderer.jsx     # エクスポート用レンダラー (/export ページ)
│   └── styles/
│       ├── global.css
│       ├── Editor.css
│       ├── Preview.css
│       ├── Sidebar.css
│       └── Timeline.css
└── dist/                      # エクスポート出力先
```

---

## フロントエンド機能

### 1. シーン選択 (`Editor.jsx`)

メインUIの左サイドバーで5種類のシーンを切り替え可能。

| シーン名 | コンポーネント | 説明 |
|----------|---------------|------|
| **静止画表示** | `StaticImageScene.jsx` | 画像をアップロードまたはURL指定して表示 |
| **動画の再現テンプレート** | `RecreationScene.jsx` | 「動画編集ソフト作ってみた！」風のアニメーション再現 |
| **自動演出モード** | `AutoScene.jsx` | テキスト台本を入力し、自動でエフェクト付きアニメーション生成 |
| **モーショングラフィックス** | `ExampleScene.jsx` | 回転する円・ダッシュ線・グラデーションタイトルのデモ |
| **円盤回転** | `DiscScene.jsx` | 画像を円盤形に切り抜いて回転表示 (シンプル/レコード盤) |

### 2. 各シーンの詳細

#### 静止画表示 (`StaticImageScene.jsx`)
- **ファイルアップロード**: `<input type="file">` → `/api/upload` で保存 (失敗時はblob URL fallback)
- **URL直接入力**: `public/` 配下パスまたは外部URL
- 画像を `object-fit: contain` で表示

#### 動画の再現テンプレート (`RecreationScene.jsx`)
- グリッド背景がフレームに応じてスクロール＋スケール
- 青いグローエフェクト
- タイトル「動画編集ソフト作ってみた！」がフェードイン + スライドアップ
- サブタイトル「【FrameScript】【React】」が遅延表示
- フレームカウンタ表示

#### 自動演出モード (`AutoScene.jsx`)
- **台本入力**: テキストを追加すると `fade` / `slide` / `bounce` からランダムにエフェクト付与
- 各テキストは2秒 (60フレーム) ずつ表示
- エフェクト:
  - `fade`: フェードイン/アウト + スケール
  - `slide`: 横スライド
  - `bounce`: バウンス + 脈動
- ループ再生対応

#### モーショングラフィックス (`ExampleScene.jsx`)
- 5つの同心円がサイン波で脈動
- ダッシュ線の円が2deg/frameで回転
- タイトル「モーショングラフィックス」がグラデーション文字でフェードイン
- プログレスバーアニメーション

#### 円盤回転 (`DiscScene.jsx`)
- **2スタイル切替**:
  - `simple` (シンプル): 画像全体を円形に切り抜いて回転
  - `vinyl` (レコード盤): レコード盤風デザイン (溝模様 + 中央ラベルのみ画像 + スピンドル穴 + 光反射)
- **画像位置調整**: X位置 (0-100%), Y位置 (0-100%), ズーム拡大 (1.0x-3.0x)
- 回転速度: 25秒で1回転 (`DISC_ROTATION_SECONDS`)

### 3. プレビュー (`Preview.jsx`)
- キャンバス領域にシーンコンポーネントを描画
- 現在フレーム番号のオーバーレイ表示

### 4. タイムライン (`Timeline.jsx`)
- 再生/停止ボタン
- 経過秒・総秒・フレーム番号表示
- フレームルーラー (10フレームごとにメジャーティック)
- クリックでシーク
- 再生ヘッド表示

### 5. 再生エンジン (`useVideoEngine.js`)
- `requestAnimationFrame` ベースの再生ループ
- FPS=30 で時間ベースのフレーム計算
- 状態: `currentFrame`, `isPlaying`, `duration`
- 操作: `play`, `pause`, `seek`, `togglePlayback`, `setDuration`

### 6. エクスポートUI (`Editor.jsx` 内 / 円盤回転シーン選択時)
- **基本の長さ (1ループ分)**: 1〜60秒スライダー
- **長尺化 (繰り返し)**: 0〜3600秒スライダー (例: 3600秒=1時間耐久動画)
- エクスポートボタン → プログレスバー + ステージ表示
- 完了後ダウンロードボタン

### 7. エクスポートレンダラー (`ExportRenderer.jsx`)
- `/export` パスで表示されるヘッドレスレンダリング用ページ
- URLクエリパラメータでシーン・画像・スタイル・フレーム指定
- `window.__setExportFrame(f)` でJSからフレーム更新 (Playwrightから呼出)
- `window.__exportReady` で準備完了シグナル

---

## バックエンド機能

### Vite Dev Server カスタムプラグイン (`vite.config.js` → `apiPlugin()`)

Viteの開発サーバーミドルウェアとして3つのAPIエンドポイントを実装。

#### API エンドポイント一覧

| メソッド | パス | 機能 |
|----------|------|------|
| `POST` | `/api/upload` | 画像ファイルアップロード |
| `POST` | `/api/export` | MP4エクスポート開始 (ストリーミング進捗) |
| `GET` | `/api/export/download/:filename` | エクスポート済みMP4ダウンロード |

#### POST `/api/upload`
- Content-Typeヘッダから拡張子判定 (png/jpg/webp/gif)
- UUID + 拡張子でファイル名生成
- `public/uploads/` に保存
- レスポンス: `{ url: "/uploads/ファイル名" }`

#### POST `/api/export`
- リクエストボディ (JSON):
  ```json
  {
    "scene": "disc",
    "image": "/uploads/xxx.png",
    "discStyle": "simple",
    "duration": 5,
    "loopDuration": 0,
    "fps": 30,
    "imageOffsetX": 50,
    "imageOffsetY": 50,
    "imageScale": 1.0
  }
  ```
- `scripts/export-video.mjs` を子プロセスとして起動
- **NDJSON ストリーミングレスポンス** で進捗通知:
  - `{ type: "stage", message: "サーバー起動中..." }` — ステージ変更
  - `{ type: "progress", current: 30, total: 150 }` — フレームキャプチャ進捗
  - `{ type: "done", filename: "export_xxx.mp4" }` — 完了
  - `{ type: "error", message: "..." }` — エラー

#### GET `/api/export/download/:filename`
- `dist/` ディレクトリからMP4ファイルを返却
- `Content-Disposition: attachment` でダウンロード

### エクスポートスクリプト (`scripts/export-video.mjs`)

Playwright + ffmpeg を使ったMP4書き出しパイプライン。

#### 処理フロー

```
1. ffmpeg 存在確認
2. Vite Dev Server 起動 (--base-url 未指定時) or 既存サーバー利用
3. Playwright (Chromium ヘッドレス) 起動
4. /export ページを開く (シーン・画像パラメータ付き)
5. フレームごとに window.__setExportFrame(f) でフレーム更新
6. #export-canvas のスクリーンショットを PNG 保存
7. 全フレーム完了後 ffmpeg で PNG連番 → MP4 (libx264, CRF 18)
8. ループ指定時: ffmpeg -stream_loop で繰り返し結合
9. 一時ファイルクリーンアップ
```

#### CLIオプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--scene` | `static` | シーン種類 |
| `--image` | (なし) | 画像パス/URL |
| `--disc-style` | `simple` | 円盤スタイル (simple/vinyl) |
| `--duration` | `5` | 基本の長さ (秒) |
| `--loop-duration` | `0` | ループ後の総秒数 (0=ループなし) |
| `--fps` | `30` | フレームレート |
| `--width` | `1920` | 出力幅 |
| `--height` | `1080` | 出力高さ |
| `--out` | `./dist/export.mp4` | 出力パス |
| `--base-url` | (なし) | 既存サーバーURL |
| `--image-offset-x` | `50` | 画像X位置 (%) |
| `--image-offset-y` | `50` | 画像Y位置 (%) |
| `--image-scale` | `1` | 画像拡大率 |

---

## スクリーンショットとUIの対応

画像 (`image copy.png`) に表示されているUIは **`Editor.jsx`** のサイドバー部分で、
**円盤回転 (disc) シーン選択時** の設定パネルを示しています。

```
シーン選択                    ← Editor.jsx: activeScene state切替
├── 静止画表示               ← StaticImageScene.jsx
├── 動画の再現テンプレート    ← RecreationScene.jsx
├── 自動演出モード           ← AutoScene.jsx
├── モーショングラフィックス  ← ExampleScene.jsx
└── 円盤回転                 ← DiscScene.jsx  ★選択中

円盤設定
├── 1. 画像とスタイル
│   ├── ファイルを選択        ← handleStaticImageFileChange → POST /api/upload
│   ├── URL入力欄            ← staticImageSrc state
│   ├── シンプル              ← discStyle='simple' → SimpleDisc
│   └── レコード盤            ← discStyle='vinyl'  → VinylDisc
│
└── 2. 位置・サイズ調整
    ├── X位置 (横) 50%       ← imageOffsetX → objectPosition
    ├── Y位置 (縦) 50%       ← imageOffsetY → objectPosition
    └── ズーム拡大 1.0x      ← imageScale   → transform: scale()

エクスポート設定
└── 出力オプション
    ├── ① 基本の長さ 26秒   ← exportDuration → duration引数
    └── ② 長尺化 (繰り返し)  ← exportLoopDuration → loopDuration引数
```

---

## データフロー図

```
[ユーザー操作]
     │
     ▼
[Editor.jsx] ─── state管理 ──→ [Preview.jsx] ──→ [各シーンコンポーネント]
     │                              ▲
     │                              │
     ├── useVideoEngine ────────────┘ (currentFrame)
     │
     ├── POST /api/upload ──→ [vite.config.js apiPlugin] ──→ public/uploads/
     │
     └── POST /api/export ──→ [vite.config.js apiPlugin]
                                    │
                                    ▼
                            [export-video.mjs]
                                    │
                            ┌───────┼───────┐
                            ▼       ▼       ▼
                        Playwright  →  PNG  →  ffmpeg  →  dist/*.mp4
                        (キャプチャ)         (エンコード)
                                                │
                                                ▼
                            GET /api/export/download/:filename
```
