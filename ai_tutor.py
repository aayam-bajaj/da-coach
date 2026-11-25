import os
import time
import streamlit as st
from google import genai
from google.genai import types

SYSTEM_PROMPT = (
    "You are a concise, practical Data Analyst interview & coding coach for freshers. "
    "Use clear structure, bullet points, and accurate SQL/Pandas examples. No fluff."
)

MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]


def _resolve_api_key(api_key: str = "") -> str:
    if api_key and api_key.strip():
        return api_key.strip()
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def stream_ai_tutor(prompt: str, api_key: str = ""):
    key = _resolve_api_key(api_key)
    if not key:
        yield "⚠️ Paste a free Gemini API key in the sidebar (from aistudio.google.com) to use the AI Tutor."
        return

    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
        max_output_tokens=850,
    )

    last_error = None
    for model_name in MODELS:
        for attempt in range(2):
            try:
                stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=prompt.strip(),
                    config=config,
                )
                yielded_any = False
                for chunk in stream:
                    if chunk.text:
                        yielded_any = True
                        yield chunk.text
                if yielded_any:
                    return
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                yield f"AI Tutor Error: {e}"
                return

    yield f"AI Tutor Error after retries: {last_error}"