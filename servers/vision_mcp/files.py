"""File-based image detection: scan a directory for usable image files."""

import os
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("vision_mcp.files")

_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif",
}


def list_images(
    directory: str = ".",
    recursive: bool = False,
) -> dict[str, Any]:
    """Scan a directory for image files and return their paths and metadata.

    Args:
      directory: Directory to scan (default: current working directory).
      recursive: Whether to search subdirectories.

    Returns dict with: ok, images (list of {path, name, size_bytes, extension}).
    """
    dir_path = Path(os.path.expanduser(directory))
    if not dir_path.is_dir():
        return {"ok": False, "error": f"Not a directory: {directory}"}

    images: list[dict[str, Any]] = []

    if recursive:
        candidates = dir_path.rglob("*")
    else:
        candidates = dir_path.iterdir()

    for p in sorted(candidates):
        if not p.is_file():
            continue
        if p.suffix.lower() not in _IMAGE_EXTENSIONS:
            continue
        try:
            stat = p.stat()
            images.append({
                "path": str(p.resolve()),
                "name": p.name,
                "size_bytes": stat.st_size,
                "extension": p.suffix.lower(),
            })
        except Exception as e:
            log.warning("Could not stat %s: %s", p, e)

    return {
        "ok": True,
        "directory": str(dir_path.resolve()),
        "count": len(images),
        "images": images,
    }
