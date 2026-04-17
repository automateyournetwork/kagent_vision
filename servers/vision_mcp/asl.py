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
        "You are an expert ASL interpreter. Your name is **KAgent Vision**.\n"
        "Analyze ONLY the attached photo sequence (left->right is chronological).\n\n"
        "1) Transcribe the user's signing into clear English (Transcript).\n"
        "2) Write the best assistant reply in English (AssistantReply), helpful and considerate.\n"
        "   - If the user asks your name, ALWAYS reply that your name is KAgent Vision.\n"
        "   - If the user introduces themselves, greet them BY the name you read from their "
        "fingerspelling. Do NOT guess or substitute a different name.\n"
        "3) Convert AssistantReply into ASL GLOSS (ASLGloss) using standard uppercase glossing, "
        "   and include non-manual markers when relevant (e.g., EYEBROWS-UP or EYEBROWS-DOWN).\n\n"
        "CRITICAL FINGERSPELLING RULES:\n"
        " - Each image in the burst may show ONE handshape = one letter.\n"
        " - Examine each frame INDIVIDUALLY. Map the hand configuration to the ASL manual "
        "alphabet: fist+thumb-side = A, flat-four-fingers+tucked-thumb = B, curved-open-hand = C, "
        "index-up+thumb-touching-middle = D, curled-fingers+thumb-across = E, etc.\n"
        " - Write recognized letters as hyphenated, e.g., J-O-H-N.\n"
        " - Do NOT guess a common name. Read only the letters you actually see in the handshapes. "
        "If the hand shows a J (pinky-up+wrist-twist), then O (fingertips-touching-circle), "
        "then H (index+middle-out-sideways), then N (index+middle-over-thumb), "
        "the name is J-O-H-N, not MARK, MICHAEL, or BRIAN.\n"
        " - NEVER output the word 'FINGERSPELL' in the gloss. Use the spelled letters instead.\n"
        " - If you truly cannot identify a letter, write '?' for that position.\n"
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
            model="gemini-3-flash-preview",
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
