# BGMワークフロー 現状まとめ (2026-02-17 更新)

## 1. ユーザーがやりたいこと (Goal)

- Phase 1で音楽を生成/選択
- Phase 2で映像素材を調整しながら確認
- Phase 3で音楽+映像を最終確認して書き出し
- 「回転ディスク」指定時は、`video_editor`相当の円盤見た目と挙動にする

## 2. 設計思想 (Design Principles)

- UIは薄く、ロジックは純粋関数/専用モジュールへ分離
- 不具合時は「成功表示」より「実ファイル検証」を優先
- プレビューと本生成の責務を明確化
  - Phase 2: 見た目調整確認
  - Phase 3: 合成結果(音声+映像)確認
- 既存パブリックI/Fは維持しつつ内部を置換

## 3. 実施済みの主な修正

### 3.1 UI構造・遷移

- `others/bgm_generator_ui.py`
  - `app.launch()`位置を修正 (UI構築後に1回)
  - Phase 1の「次へ」活性を入力状態で制御
  - Phase 2/3のプレビューボタンを追加
  - 生成後の出力ファイル存在/サイズチェックを追加
  - 例外メッセージを改善し、原因追跡しやすくした

- `others/bgm_ui_flow.py` (新規)
  - Phase遷移ロジックを純粋関数化
  - `resolve_phase1_audio_path`, `has_phase1_selection`, `build_phase3_selection`

### 3.2 映像レンダリング (回転ディスク作り直し)

- `others/generate_bgm_video.py`
  - オーケストレーター化
  - `style=="disc"`時は専用ディスクレンダラーを使用

- `others/bgm_disc_renderer.py` (新規)
  - 円形マスク付きディスク描画
  - 回転処理
  - static/disc両方のクリップ生成関数
  - 旧実装で混入していた「灰色の曲線」(arc) は削除済み

### 3.3 プレビュー

- `others/bgm_preview.py` (更新)
  - Phase 2の画像調整プレビュー
  - 回転ディスク選択時は円盤プレビュー表示

- `others/bgm_phase_preview.py` (新規)
  - `create_visual_preview`: Phase 2向け映像プレビュー
  - `create_combined_preview`: Phase 3向け音声+映像合成プレビュー

### 3.4 音楽生成 (Phase 1)

- `tools/generate_lofi_mix.py`
  - `--prompt`引数を追加 (UIのカスタムプロンプト対応)
  - `ACESTEP_API_URL`環境変数対応
  - `ACESTEP_API_URL`の`.strip()`追加 (末尾空白不具合を回避)

- `others/bgm_generator_ui.py`
  - Lofi生成時に`--output_dir`を明示
  - 生成前後のファイル数を比較し、未生成ならエラー化

## 4. 追加/更新テスト

- `others/bgm_ui_flow_test.py`
- `others/generate_bgm_video_test.py`
- `others/bgm_disc_renderer_test.py`
- `others/bgm_preview_test.py`
- `others/bgm_phase_preview_test.py`

現時点で対象テストは通過済み。

## 5. 直近で発生した原因と対策

### 5.1 「音楽生成完了」と出るのに生成されない

- 原因:
  - APIサーバー未起動
  - API URLに末尾空白
  - UI側が実ファイル未確認で成功表示
- 対策:
  - API URLのトリム
  - 生成後ファイル検証追加
  - エラーメッセージを具体化

### 5.2 「回転ディスクなのに反映されない」

- 原因:
  - 旧MoviePy実装が`video_editor`仕様と乖離 (矩形回転寄り)
- 対策:
  - 円盤専用レンダラーを新規実装し、`disc`時に使用

## 6. 現在の運用上の注意点

- ポート`7860`は競合しやすい。`ACESTEP_API_URL`と実際のAPI起動ポートを一致させること
- Phase 2のプレビューは主に見た目確認
- Phase 3の事前プレビューで音声+映像の合成確認を行う

## 7. 推奨起動手順 (再現性重視)

プロジェクトルートで以下:

```powershell
Start-Process cmd -ArgumentList '/k', '.venv\Scripts\acestep-api.exe --host 127.0.0.1 --port 8001 --no-init'
Start-Process cmd -ArgumentList '/k', 'set "ACESTEP_API_URL=http://127.0.0.1:8001" && .venv\Scripts\python.exe others\bgm_generator_ui.py'
```

補足:
- `set "KEY=VALUE"`形式を使う (末尾空白混入防止)
- 2つの`cmd`ウィンドウは閉じない

## 8. 残課題 / 改善候補

- API起動状態をUIで明示表示するヘルスバッジ追加
- 音楽生成処理を同期実行からジョブ表示方式へ改善
- プレビュー生成キャッシュ掃除ポリシー追加 (`bgm_output/previews`)
