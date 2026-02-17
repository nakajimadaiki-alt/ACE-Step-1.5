# 進捗・実装・課題まとめ

## 1. 現状の進捗 (Status)

- **BGM生成機能**: 音楽生成 (Lofi) と動画生成 (MoviePy) のコアロジックは実装済み。
- **UI実装**: Gradioを用いた3段階ウィザード形式のUI (`bgm_generator_ui.py`) を実装。日本語化完了。
- **設定ファイルの整理**: スクリプトを `others/` ディレクトリへ移動し、パス設定を更新。
- **画像調整機能**: UIに「サイズ」「位置(X,Y)」スライダーを追加したが、現在**動作不全**。

## 2. 実装内容 (Implementation Details)

### Frontend: `others/bgm_generator_ui.py`

- **フレームワーク**: Gradio
- **構成**:
  - **Phase 1**: 音楽選択 (既存ファイル or AI生成)
  - **Phase 2**: 映像選択 (動画ループ or 静止画)
    - 静止画モードに「回転ディスク」と「固定表示」を用意。
    - **新機能**: 画像の拡大率 (`image_scale`) と位置オフセット (`image_offset_x`, `image_offset_y`) の入力欄を追加。
  - **Phase 3**: プレビューと生成実行

### Backend: `others/generate_bgm_video.py`

- **ライブラリ**: MoviePy v2.0+
- **機能**:
  - 音声と映像の合成。
  - 静止画モード時、黒背景 (1920x1080) 上での画像合成 (`CompositeVideoClip`) を実装。
  - 画像の回転アニメーション (`Rotate` エフェクト)。
  - **新機能**: 引数として `scale`, `offset_x`, `offset_y` を受け取り、`ColorClip` (背景) と `ImageClip` (前景) を合成するロジックを追加。

## 3. ユーザーの困っていること (Legacy Issues)

1. **機能不全**: 「画像の位置調整がない」という要望に対し実装を行ったが、エラー (`AttributeError`) で動かない。
2. **繰り返すエラー**: 修正対応後もエラーが解消されず、ストレスが溜まっている。
3. **信頼性の欠如**: 「直した」と言ったのに直っていない。

## 4. 直近のエラー原因 (Diagnosis)

- **エラー内容**: `AttributeError: ... object has no attribute 'page'`
- **推定原因**: MoviePy v2.0系における `CompositeVideoClip` と `ColorClip`/`ImageClip` の合成処理において、属性の初期化不足またはバージョン非互換な記述がある可能性が高い。特に `ColorClip` の生成や `CompositeVideoClip` へのクリップの渡し方で問題が起きていると考えられる。

---

## システムワークフローと接続図

このシステムは、Web UI (Frontend) でユーザー入力を受け付け、CLIツール (Backend) を呼び出して動画を生成する構成になっています。

## 全体フロー図

```mermaid
graph TD
    User[ユーザー] -->|操作| UI[Gradio UI\n(others/bgm_generator_ui.py)]
    
    subgraph "Phase 1: Audio"
        UI -->|Generate Lofi| LofiScript[Lofi Generator\n(tools/generate_lofi_mix.py)]
        LofiScript -->|Save| AudioFiles[audio/*.mp3]
        AudioFiles -->|Select| UI
    end
    
    subgraph "Phase 2: Visual"
        UI -->|Upload/Select| VideoFiles[video/*.mp4]
        UI -->|Upload| ImageFiles[images/*.jpg/png]
        UI -->|Settings| Params[パラメータ設定\n(回転, サイズ, 位置)]
    end
    
    subgraph "Phase 3: Generation (Backend)"
        UI -->|Call Logic| Wrapper[final_generation_wrapper]
        Wrapper -->|Function Call| GenScript[generate_bgm_video.py\n(generate_bgm_video関数)]
        
        GenScript -->|Process| MoviePy[MoviePy Engine]
        
        MoviePy -->|Scaling/Offset| Composite[CompositeVideoClip\n(背景+画像合成)]
        MoviePy -->|Rotation| Rotate[Rotate Effect]
        MoviePy -->|Audio Mix| AudioMix[Audio Loop/Mix]
    end
    
    MoviePy -->|Output| FinalVideo[bgm_output/*.mp4]
    FinalVideo -->|Display| UI
```

## Frontend と Backend の接続詳細

### 接続ポイント

`bgm_generator_ui.py` 内の `final_generation_wrapper` 関数が、`generate_bgm_video.py` の `generate_bgm_video` 関数を直接インポートして呼び出しています。

### データフロー (引数の受け渡し)

| UI Input (Gradio) | Wrapper引数 | Backend引数 (`generate_bgm_video`) | 説明 |
| :--- | :--- | :--- | :--- |
| **Selected Audio** | `audio_path` | `audio_path` | 音声ファイルのパス |
| **Visual Mode** | `visual_mode` | (内部ロジックで分岐) | 動画か静止画かの判定 |
| **Output Name** | `output_filename` | `output_path` | 出力先パス (bgm_output/...) |
| **Video File** | `video_path` | `video_path` | 動画ループ時の素材 |
| **Image File** | `image_path` | `image_path` | 静止画モード時の素材 |
| **回転周期 (Slider)** | `rotation_period` | `rotation_speed` | `1.0 / rotation_period` で計算 |
| **サイズ (Slider)** | `image_scale` | `image_scale` | 画像のリサイズ倍率 (例: 1.0) |
| **位置 X (Slider)** | `image_offset_x` | `image_offset_x` | 中心からのX座標ズレ (px) |
| **位置 Y (Slider)** | `image_offset_y` | `image_offset_y` | 中心からのY座標ズレ (px) |

### 現在の問題点

この接続部分において、MoviePyの合成処理 (`CompositeVideoClip`) で内部エラーが発生しており、Backend側で処理が落ちている状態です。
