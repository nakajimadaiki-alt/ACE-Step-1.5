# noUI 楽曲・動画自動生成ガイド

UIを使わずに `.txt` ファイルだけで音楽生成→動画合成を完全自動実行する手法。

---

## 全体フロー

```
songs/my_song.txt   (設定ファイルを書く)
        ↓
python tools/auto_generate.py songs/my_song.txt
        ↓
[1/2] ACE-Step API で音楽生成  →  .cache/ に WAV を保存
        ↓
[2/2] MoviePy で動画レンダリング
        ↓
bgm_output/my_song.mp4  (完成)
```

---

## 前提: APIサーバーの起動

**毎回セッション開始時に必須。** 新しい cmd ウィンドウが開くので閉じないこと。

```powershell
# PowerShell から実行 (プロジェクトルートで)
Start-Process cmd -ArgumentList '/k', '.venv\Scripts\acestep-api.exe --host 127.0.0.1 --port 8001'
```

- 初回起動はモデルロード（約9.4GB）で **1〜3分** かかる
- ポートが競合する場合は `8001` を別の番号に変えて `ACESTEP_API_URL` も合わせること

---

## 実行コマンド

```cmd
set PYTHONIOENCODING=utf-8
set ACESTEP_API_URL=http://127.0.0.1:8001
.venv\Scripts\python.exe tools\auto_generate.py songs\my_song.txt
```

複数ファイルを一括処理する場合:

```cmd
.venv\Scripts\python.exe tools\auto_generate.py songs\song_a.txt songs\song_b.txt
```

独立した cmd ウィンドウで実行する場合（推奨・タイムアウトなし）:

```powershell
Start-Process cmd -ArgumentList '/k', 'set PYTHONIOENCODING=utf-8 && set ACESTEP_API_URL=http://127.0.0.1:8001 && .venv\Scripts\python.exe tools\auto_generate.py songs\my_song.txt'
```

---

## .txt 設定ファイルの書き方

`songs/` フォルダに `.txt` を置く。`songs/example.txt` がテンプレート。

### 画像・動画パスの書き方

パスは **`.txt` ファイルの場所からの相対パス** で解決されます。

| .txt の置き場所 | `image.png` を指定する書き方 |
|---------------|--------------------------|
| `songs/` フォルダ内 | `image = ../image.png` |
| プロジェクトルート直下 | `image = ./image.png` |
| どこからでも確実 | `image = C:/Users/.../image.png`（絶対パス） |

### 最小構成

```
caption = chill lo-fi hip hop, warm piano, soft drums
duration = 180
visual  = video
output  = my_lofi
```

### 全オプション一覧

```
# ===== 音楽 =====

caption = <スタイル・楽器・雰囲気の説明>   # 必須
duration = 180                              # 曲の長さ (秒)
bpm = 75                                    # 省略可: モデルが自動決定
keyscale = C Major                          # 省略可: 例 "Am", "G Major"
seed = -1                                   # -1=ランダム、固定値で再現

# 音質チューニング
steps = 60                                  # 推論ステップ数 (30〜100)
guidance_scale = 4.5                        # ガイダンス強度 (3.5〜5.0推奨)

# 後処理 (音をまろやかにする)
post_process = true                         # ローパス + ノーマライズを適用
lpf_cutoff = 10000                          # ローパス遮断周波数 Hz (デフォルト10000)


# ===== 映像 =====

visual = video                              # video | disc | static

# visual=video のとき
video = ./video_editor/dist/export.mp4     # 省略すると video_editor/dist/ から自動選択

# visual=disc または static のとき
image = ./assets/cover.png                  # 必須

rotation_period = 10                        # disc: 1回転の秒数
image_scale = 1.0                           # 画像の拡大率
image_offset_x = 0                          # 水平位置オフセット (px)
image_offset_y = 0                          # 垂直位置オフセット (px)


# ===== 出力 =====

output = my_video                           # 省略するとファイル名と同名。.mp4 は自動付与


# ===== 歌詞 (ボーカル曲のみ) =====

lyrics_file = ./songs/lyrics/my_lyrics.txt  # 外部ファイルで管理する場合

# または .txt 内にインラインで書く:
[lyrics]
[Verse]
歌詞をここに書く

[Chorus]
サビをここに書く
[/lyrics]
```

---

## 音質チューニングの指針

### なぜとげとげしい音になるか

| 原因 | 症状 | 対処 |
|------|------|------|
| `guidance_scale` が高い (7以上) | 高周波歪み、ざらつき | 3.5〜5.0 に下げる |
| `steps` が少ない (25以下) | ノイズが残る、粗い質感 | 60 以上に増やす |
| 高音域の後処理なし | キンキンした高音が残る | `post_process = true` を追加 |
| captionに柔らかさの記述なし | モデルが硬い音を生成 | 下記の言葉を追加する |

### caption に入れると音が柔らかくなる言葉

```
warm, mellow, soft, rounded transients, muffled, analog warmth,
vintage, tape saturation, low-pass filtered, gentle, airy
```

### 用途別の推奨設定

| 用途 | steps | guidance_scale | post_process |
|------|-------|----------------|--------------|
| Lo-fi BGM | 60 | 4.0 | true (8000Hz) |
| ポップス | 60 | 4.5 | false |
| 環境音・アンビエント | 80 | 3.5 | true (6000Hz) |
| 速度優先 (試聴用) | 30 | 4.5 | false |

---

## 出力ファイルの場所

| ファイル | 場所 |
|---------|------|
| 完成動画 | `bgm_output/<output>.mp4` |
| 生成音声 (WAV) | `.cache/acestep/tmp/api_audio/<uuid>.wav` |
| 後処理済み音声 | `.cache/acestep/tmp/api_audio/<uuid>_processed.wav` |

---

## トラブルシューティング

### `ERROR: ACE-Step API に接続できません`

→ APIサーバーが起動していない。上記の起動コマンドを実行。

### `Audio file not found`

→ `auto_generate.py` が古いバージョン。`_resolve_audio_path()` 関数が含まれているか確認。

### `Model not initialized`

→ APIサーバーを `--no-init` フラグなしで起動し直す。起動に1〜3分かかる。

### 動画レンダリングが遅い

→ `test_duration = 20` を設定すると冒頭20秒だけ生成してテストできる。

### 生成に失敗する (status=-1)

→ `.cache/acestep/` のログを確認。VRAMが不足している可能性あり。

---

## 関連ファイル

| ファイル | 説明 |
|---------|------|
| `tools/auto_generate.py` | メインスクリプト |
| `songs/example.txt` | 設定ファイルのテンプレート |
| `app/generate_bgm_video.py` | 動画合成ロジック |
| `app/bgm_disc_renderer.py` | 回転ディスク描画 |
| `tools/generate_lofi_mix.py` | Lofi専用バッチ生成 (複数曲ミックス) |
