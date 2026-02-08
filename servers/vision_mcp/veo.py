"""Veo: AI video generation via Google Veo 3 API."""

import os
import time
import logging
import mimetypes
from pathlib import Path
from typing import Any

log = logging.getLogger("vision_mcp.veo")


def veo_generate_video(
    prompt: str,
    negative_prompt: str = "",
    out_dir: str = "outputs",
    model: str = "veo-3.1-generate-preview",
    image_path: str | None = None,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    seed: int | None = None,
    poll_seconds: int = 8,
    max_wait_seconds: int = 900,
) -> dict[str, Any]:
    """Generate video from a text prompt, optionally conditioned on an input image.
    Saves MP4 files to out_dir and returns their paths.

    Args:
      prompt: Text instruction for the video.
      negative_prompt: Things to avoid in the video.
      out_dir: Directory to write generated files.
      model: Veo model identifier.
      image_path: Optional image file path for image-conditioned generation.
      aspect_ratio: "16:9" or "9:16".
      resolution: e.g. "720p", "1080p".
      seed: Optional seed for reproducibility.
      poll_seconds: Seconds between polling attempts.
      max_wait_seconds: Maximum wait time before timeout.
    """
    try:
        from google import genai
        from google.genai import types as gtypes
    except Exception as e:
        return {"ok": False, "error": f"google-genai not installed: {e}"}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"ok": False, "error": "GEMINI_API_KEY not set in environment"}

    client = genai.Client(api_key=api_key)
    out_dir_p = Path(os.path.expanduser(out_dir))
    out_dir_p.mkdir(parents=True, exist_ok=True)

    image_obj = None
    if image_path:
        try:
            with open(image_path, "rb") as f:
                data = f.read()
            mt, _ = mimetypes.guess_type(image_path)
            image_obj = gtypes.Image(image_bytes=data, mime_type=mt or "image/png")
        except Exception as e:
            return {"ok": False, "error": f"read image failed: {e}"}

    cfg = gtypes.GenerateVideosConfig(
        negative_prompt=negative_prompt or None,
        aspect_ratio=aspect_ratio or None,
        resolution=resolution or None,
        seed=seed,
    )

    try:
        op = client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=image_obj,
            config=cfg,
        )
    except Exception as e:
        return {"ok": False, "error": f"veo start failed: {e}"}

    waited = 0
    try:
        while not op.done:
            if waited >= max_wait_seconds:
                return {"ok": False, "error": f"timeout after {max_wait_seconds}s"}
            time.sleep(max(1, int(poll_seconds)))
            waited += poll_seconds
            op = client.operations.get(op)
    except Exception as e:
        return {"ok": False, "error": f"veo poll failed: {e}"}

    vids = getattr(op.response, "generated_videos", []) or []
    if not vids:
        return {"ok": False, "error": "no videos in response"}

    saved: list[str] = []
    for idx, gv in enumerate(vids):
        client.files.download(file=gv.video)
        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int((time.time() % 1) * 1000)
        fpath = out_dir_p / f"veo_{ts}_{ms:03d}_{idx:02d}.mp4"
        gv.video.save(str(fpath))
        saved.append(str(fpath))

    return {
        "ok": True,
        "paths": saved,
        "model": model,
        "seconds_waited": waited,
        "image_used": bool(image_obj),
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "seed": seed,
    }
