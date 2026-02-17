# BGM Generator Wizard

ACE-Step API を利用した **AI音楽生成** と **映像合成** のワークフローツールです。
3つのフェーズを順に進めるだけで、作業用BGM動画 (MP4) を作成できます。

---

## 目次

- [概要](#概要)
- [必要環境](#必要環境)
- [セットアップ](#セットアップ)
- [起動方法](#起動方法)
- [使い方](#使い方)
  - [Phase 1: 音楽の準備](#phase-1-音楽の準備)
  - [Phase 2: 映像の選択](#phase-2-映像の選択)
  - [Phase 3: 生成・プレビュー](#phase-3-生成プレビュー)
- [CLI で音楽だけ生成する](#cli-で音楽だけ生成する)
- [ディレクトリ構成](#ディレクトリ構成)
- [設定・環境変数](#設定環境変数)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

```
┌─────────────────────────────────────────────────────┐
│  Phase 1          Phase 2          Phase 3          │
│  音楽の準備  ───►  映像の選択  ───►  生成・確認     │
│                                                     │
│  ・ライブラリ選択    ・動画ループ      ・テストモード │
│  ・AI 生成           ・回転ディスク    ・本番書き出し │
│  ・ファイルアップ    ・静止画固定      ・事前プレビュー│
└─────────────────────────────────────────────────────┘
```

### 主な機能

| 機能 | 説明 |
|------|------|
| **AI 音楽生成** | ACE-Step API でプロンプトから音楽を自動生成。Lofi Hip Hop をデフォルトで作成し、自由なジャンル指定も可能 |
| **映像モード** | 動画ループ / 回転ディスク / 静止画固定 の3種類から選択 |
| **回転ディスク** | 画像を円形にマスクしてレコード風に回転する映像を生成 |
| **リアルタイムログ** | 音楽生成中の進捗をUI上でリアルタイムに表示 |
| **プレビュー** | Phase 2 で映像のみ、Phase 3 で音声+映像の合成結果を事前確認 |
| **API ヘルスバッジ** | ACE-Step サーバーの接続状態を常時表示 (30秒ごと自動更新) |

---

## 必要環境

- **Python** 3.10 以上
- **ACE-Step API サーバー** (音楽生成に必要)
- **VRAM** 4GB 以上の GPU (ACE-Step 推奨)

### Python パッケージ

```
gradio>=4.0
moviepy>=2.0
Pillow
requests
pydub
numpy
```

---

## セットアップ

```bash
# 1. リポジトリのクローン (未取得の場合)
git clone https://github.com/<your-repo>/ACE-Step-1.5.git
cd ACE-Step-1.5

# 2. 仮想環境の作成 & 依存インストール
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements/requirements.txt
```

---

## 起動方法

2つのプロセスを起動します。

### Windows (PowerShell)

```powershell
# ターミナル 1: ACE-Step API サーバー
Start-Process cmd -ArgumentList '/k', '.venv\Scripts\acestep-api.exe --host 127.0.0.1 --port 8001 --no-init'

# ターミナル 2: BGM Generator UI
Start-Process cmd -ArgumentList '/k', 'set "ACESTEP_API_URL=http://127.0.0.1:8001" && .venv\Scripts\python.exe others\bgm_generator_ui.py'
```

### Linux / macOS

```bash
# ターミナル 1
acestep-api --host 127.0.0.1 --port 8001 --no-init

# ターミナル 2
ACESTEP_API_URL=http://127.0.0.1:8001 python others/bgm_generator_ui.py
```

ブラウザが自動で開き、Gradio UI が表示されます。
画面上部の **ヘルスバッジ** が `API: Online` (緑) になっていれば準備完了です。

> **注意**: `set "KEY=VALUE"` のように二重引用符で囲んでください。`set KEY=VALUE ` のように末尾に空白が入ると API 接続に失敗します。

---

## 使い方

### Phase 1: 音楽の準備

音楽ファイルを用意する方法は3つあります。

| 方法 | 手順 |
|------|------|
| **ライブラリから選択** | ドロップダウンから既存ファイルを選択 |
| **アップロード** | WAV / MP3 ファイルをドラッグ&ドロップ |
| **AI 生成** | 「新しく生成する (AI)」タブでプロンプト・曲数・長さを指定して生成 |

#### AI 生成の設定

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| 生成プロンプト | _(空欄 = Lofi Hip Hop)_ | ジャンル・雰囲気を自由に記述 (例: `chill beats, jazz piano`) |
| 曲数 | 3 | 1〜20 トラックを生成してクロスフェードで1本にミックス |
| 1曲あたりの長さ | 120秒 | 60〜300秒 |

生成が始まると **生成ログ** にリアルタイムで進捗が表示されます。
完了後、ドロップダウンに新しいファイルが自動追加されます。

---

### Phase 2: 映像の選択

3つの映像モードから選択します。

#### 動画ループ (Video Loop)

既存の動画素材をループ再生します。
`video_editor/dist/` 内の動画がドロップダウンに表示されます。

#### 回転ディスク (Rotating Disk)

アップロードした画像を **円形にマスク** してレコードのように回転させます。

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| 回転周期 | 10秒 | ディスクが1回転するのにかかる秒数 |

#### 静止画 - 固定表示 (Static Image)

アップロードした画像を黒背景の中央に配置します。

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| サイズ (倍率) | 1.0x | 0.1〜3.0倍 |
| 位置 X | 0 | -960 〜 +960 px |
| 位置 Y | 0 | -540 〜 +540 px |

**「Phase 2 プレビュー更新」** ボタンで映像のみの短いプレビュー (4秒) を確認できます。

---

### Phase 3: 生成・プレビュー

Phase 1 と Phase 2 の設定内容が **サマリー** に表示されます。

| 操作 | 説明 |
|------|------|
| **事前プレビュー** | 音声+映像を合成した8秒のプレビュー動画を確認 |
| **テストモード** | 冒頭20秒のみを高速に書き出し (動作確認用) |
| **本番生成** | フル尺の BGM 動画を書き出し |

出力先: `bgm_output/<ファイル名>.mp4`

---

## CLI で音楽だけ生成する

UI を使わずコマンドラインから音楽生成のみ行えます。

```bash
python tools/generate_lofi_mix.py \
  --num_tracks 5 \
  --track_duration 180 \
  --output_dir lofi_mix_output \
  --prompt "chill ambient, soft piano, rain sounds"
```

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `--num_tracks` | 15 | 生成するトラック数 |
| `--track_duration` | 240 | 1トラックあたりの秒数 |
| `--output_dir` | `lofi_mix_output` | 出力ディレクトリ |
| `--prompt` | _(Lofi Hip Hop)_ | 全トラック共通のプロンプト |

生成されたトラックは **ローパスフィルタ (10kHz)** → **クロスフェード (5秒)** → **ノーマライズ** の順で処理され、1本の WAV ファイルとして出力されます。

---

## ディレクトリ構成

```
ACE-Step-1.5/
├── others/                         # BGM ワークフロー本体
│   ├── bgm_generator_ui.py        # Gradio UI (メイン)
│   ├── bgm_ui_flow.py             # Phase 遷移ロジック (純粋関数)
│   ├── bgm_health.py              # API ヘルスチェック
│   ├── bgm_cache.py               # プレビューキャッシュ管理
│   ├── bgm_preview.py             # 画像調整プレビュー
│   ├── bgm_phase_preview.py       # Phase 2/3 動画プレビュー
│   ├── bgm_disc_renderer.py       # 回転ディスク レンダラー
│   └── generate_bgm_video.py      # 動画生成オーケストレーター
│
├── tools/
│   └── generate_lofi_mix.py       # Lofi 音楽生成 CLI
│
├── lofi_mix_output/                # 生成された音楽ファイル
├── video_editor/dist/              # 動画ループ素材
└── bgm_output/                     # 最終出力
    └── previews/                   # プレビュー一時ファイル
```

---

## 設定・環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `ACESTEP_API_URL` | `http://127.0.0.1:7860` | ACE-Step API サーバーの URL |

---

## トラブルシューティング

### ヘルスバッジが `API: Offline` (赤) のまま

- ACE-Step API サーバーが起動しているか確認
- `ACESTEP_API_URL` と実際のサーバーポートが一致しているか確認
- ポート `7860` は Gradio のデフォルトポートと競合しやすいため、`8001` など別ポートを推奨

### 「音楽を生成」しても何も出力されない

- 生成ログを確認してください。`Error: ACE-Step server is not running` が表示されていればサーバー未起動です
- `ACESTEP_API_URL` の末尾に空白が混入していないか確認 (`set "KEY=VALUE"` 形式を使用)

### 動画生成が失敗する

- 音声ファイルが正しく選択されているか確認 (Phase 1 に戻って再選択)
- 画像モード選択時に画像がアップロードされているか確認
- コンソールの `DEBUG: Calling generate_bgm_video with:` の出力でパラメータを確認

### プレビューファイルが溜まる

- UI 下部の **「Preview Cache」** アコーディオンから手動でクリーンアップ可能
- プレビュー生成時に自動で古いファイルが削除されます (最大20個を保持)
