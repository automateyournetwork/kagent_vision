"""ASL understanding: burst of frames -> transcript, assistant reply, ASL gloss."""

import os
import json
import logging
import mimetypes
from typing import Any

log = logging.getLogger("vision_mcp.asl")


def asl_understand(
    paths: list[str],
    style_hint: str = "friendly, concise",
) -> dict[str, Any]:
    """Use Gemini (multimodal) to:
      1) Transcribe the user's signing (English).
      2) Propose the best assistant reply (English).
      3) Return an ASL GLOSS (UPPERCASE gloss) of that reply for signing.

    Args:
      paths: List of image file paths in chronological order.
      style_hint: Style guidance for the assistant reply.

    Returns dict with: ok, transcript, assistant_reply, asl_gloss.
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

    instruction = (
        "You are an expert ASL interpreter.\n"
        "Analyze ONLY the attached photo sequence (left->right is chronological).\n"
        "1) Transcribe the user's signing into clear English (Transcript).\n"
        "2) Write the best assistant reply in English (AssistantReply), helpful and considerate.\n"
        "3) Convert AssistantReply into ASL GLOSS (ASLGloss) using standard uppercase glossing, "
        "   and include non-manual markers when relevant (e.g., EYEBROWS-UP or EYEBROWS-DOWN).\n"
        "IMPORTANT NAME RULES:\n"
        " - If the user fingerspells their name and you can infer letters, write them as "
        "hyphenated letters, e.g., J-O-H-N.\n"
        " - NEVER output the word 'FINGERSPELL' in the gloss. Use the spelled letters instead.\n"
        " - If you cannot infer the letters, use '[FINGERSPELLED-NAME]' as a placeholder.\n"
        'Return strict JSON: {"Transcript":"...","AssistantReply":"...","ASLGloss":"..."} '
        "with no extra text."
    )

    if style_hint:
        instruction += f"\nStyle hint for AssistantReply: {style_hint}"

    parts: list = [gtypes.Part.from_text(text=instruction)]
    for p in paths:
        try:
            with open(p, "rb") as f:
                data = f.read()
            mt, _ = mimetypes.guess_type(p)
            parts.append(gtypes.Part.from_bytes(data=data, mime_type=mt or "image/jpeg"))
        except Exception as e:
            return {"ok": False, "error": f"read frame failed '{p}': {e}"}

    raw = "{}"
    try:
        res = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[gtypes.Content(role="user", parts=parts)],
            config=gtypes.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        raw = getattr(res, "text", "") or "{}"
        obj = json.loads(raw)
    except Exception:
        obj = {"Transcript": "", "AssistantReply": "", "ASLGloss": ""}
        try:
            if raw and isinstance(raw, str):
                obj["AssistantReply"] = raw.strip()
        except Exception:
            pass

    return {
        "ok": True,
        "transcript": (obj.get("Transcript") or "").strip(),
        "assistant_reply": (obj.get("AssistantReply") or "").strip(),
        "asl_gloss": (obj.get("ASLGloss") or "").strip(),
    }
