"""Nano Banana: AI image generation / transformation via Google Gemini Image Generation API."""

import os
import time
import logging
import mimetypes
from pathlib import Path
from typing import Any

log = logging.getLogger("vision_mcp.banana")


def banana_generate(
    prompt: str,
    input_paths: list[str] | None = None,
    out_dir: str = "outputs",
    model: str = "gemini-3-pro-image-preview",
    n: int = 1,
) -> dict[str, Any]:
    """Generate image(s) from a text prompt, optionally guided by input image(s).
    Saves files to out_dir and returns their paths.

    Args:
      prompt: Text instruction for the model.
      input_paths: Optional list of image file paths (image-to-image).
      out_dir: Directory to write generated files.
      model: Gemini multimodal image generation model.
      n: Desired number of images (best-effort; stream may emit 1+).
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

    parts: list = [gtypes.Part.from_text(text=prompt)]
    input_paths = input_paths or []
    for p in input_paths:
        try:
            with open(p, "rb") as f:
                data = f.read()
            mt, _ = mimetypes.guess_type(p)
            if not mt:
                mt = "image/jpeg"
            parts.append(gtypes.Part.from_bytes(data=data, mime_type=mt))
        except Exception as e:
            return {"ok": False, "error": f"Failed to read input image '{p}': {e}"}

    contents = [gtypes.Content(role="user", parts=parts)]
    config = gtypes.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])

    out_dir_p = Path(os.path.expanduser(out_dir))
    out_dir_p.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    texts: list[str] = []
    file_index = 0

    try:
        response = client.models.generate_content(
            model=model, contents=contents, config=config
        )
    except Exception as e:
        return {"ok": False, "error": f"Generation failed: {e}"}

    # Extract images and text from response parts
    cands = getattr(response, "candidates", []) or []
    for cand in cands:
        if not cand.content or not cand.content.parts:
            continue
        for part in cand.content.parts:
            # Check for text
            if getattr(part, "text", None):
                texts.append(part.text)

            # Check for inline image data
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                mt = getattr(inline, "mime_type", "image/png")
                ext = mimetypes.guess_extension(mt) or ".png"
                ts = time.strftime("%Y%m%d_%H%M%S")
                ms = int((time.time() % 1) * 1000)
                fname = f"banana_{ts}_{ms:03d}_{file_index:02d}{ext}"
                fpath = out_dir_p / fname
                file_index += 1
                try:
                    with open(fpath, "wb") as f:
                        f.write(inline.data)
                    saved.append(str(fpath))
                    log.info("Banana saved: %s", fpath)
                except Exception as e:
                    return {
                        "ok": False,
                        "error": f"Failed to save generated image: {e}",
                    }

    if not saved:
        return {
            "ok": False,
            "error": "Model returned no images. It may have returned text only.",
            "text": "\n".join(texts).strip() if texts else "",
            "model": model,
        }

    return {
        "ok": True,
        "paths": saved,
        "text": "\n".join(texts).strip() if texts else "",
        "model": model,
        "count": len(saved),
        "out_dir": str(out_dir_p),
        "guided_by": input_paths,
    }
