"""BGM UIの画面遷移に使う純粋関数群。"""

from __future__ import annotations

import os
from typing import Any


def _as_path(value: Any) -> str | None:
    """Gradio入力値をファイルパス文字列へ正規化する。

    Args:
        value: `Dropdown`/`File`由来の入力値。

    Returns:
        正規化されたファイルパス。空の場合は `None`。
    """
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    return None


def has_phase1_selection(dropdown_val: Any, upload_val: Any) -> bool:
    """Phase 1で音声選択済みかを判定する。"""
    return resolve_phase1_audio_path(dropdown_val, upload_val) is not None


def resolve_phase1_audio_path(dropdown_val: Any, upload_val: Any) -> str | None:
    """Phase 1の選択結果から音声ファイルパスを決定する。

    優先順は「アップロード > ドロップダウン」。
    """
    upload_path = _as_path(upload_val)
    if upload_path:
        return upload_path
    return _as_path(dropdown_val)


def build_phase3_selection(
    mode: str,
    video_dropdown_path: Any,
    video_upload_path: Any,
    image_upload_path: Any,
    audio_path: Any,
) -> tuple[str, str | None, str | None, str]:
    """Phase 3へ渡す映像選択情報と要約文を生成する。

    Raises:
        ValueError: 必須入力が欠けている場合。
    """
    selected_audio_path = _as_path(audio_path)
    if not selected_audio_path:
        raise ValueError("音楽ファイルを選択してください。")

    video_path = _as_path(video_upload_path) or _as_path(video_dropdown_path)
    image_path = _as_path(image_upload_path)
    audio_name = os.path.basename(selected_audio_path)
    summary = f"**選択された音楽**: `{audio_name}`\n\n"

    if mode == "動画ループ (Video Loop)":
        if not video_path:
            raise ValueError("動画を選択してください。")
        summary += f"**選択された映像**: 動画ループ (`{os.path.basename(video_path)}`)"
        return mode, video_path, None, summary

    if not image_path:
        raise ValueError("画像をアップロードしてください。")
    mode_name = "回転ディスク" if "回転" in mode else "固定表示"
    summary += f"**選択された映像**: 静止画 - {mode_name} (`{os.path.basename(image_path)}`)"
    return mode, video_path, image_path, summary
