"""Preview cache management utilities for bgm_output/previews."""

import glob
import os

DEFAULT_MAX_FILES = 20


def cleanup_previews(
    preview_dir: str,
    max_files: int = DEFAULT_MAX_FILES,
) -> int:
    """Delete oldest preview files exceeding *max_files* limit.

    Returns the number of files deleted.
    """
    files = glob.glob(os.path.join(preview_dir, "*.mp4"))
    files.sort(key=os.path.getmtime, reverse=True)

    to_delete = files[max_files:]
    deleted = 0
    for f in to_delete:
        try:
            os.remove(f)
            deleted += 1
        except OSError:
            pass
    return deleted


def get_preview_stats(preview_dir: str) -> dict:
    """Return ``{"count": int, "size_mb": float}`` for preview dir."""
    if not os.path.exists(preview_dir):
        return {"count": 0, "size_mb": 0.0}
    files = glob.glob(os.path.join(preview_dir, "*.mp4"))
    total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
    return {
        "count": len(files),
        "size_mb": round(total_size / (1024 * 1024), 1),
    }
