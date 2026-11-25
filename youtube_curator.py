import yt_dlp
import streamlit as st

@st.cache_data(ttl=86400)  # Cache results for 24h so repeat clicks are instant
def fetch_top_youtube_resources(query: str, max_results: int = 3):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }
    search_url = f"ytsearch{max_results}:{query} playlist"
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            for entry in info.get("entries", []):
                results.append({
                    "title": entry.get("title", "Untitled"),
                    "url": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    "channel": entry.get("uploader") or entry.get("channel") or "YouTube",
                    "views": entry.get("view_count") or 0,
                })
    except Exception as e:
        return [{"title": f"Search error: {e}", "url": "", "channel": "", "views": 0}]
    return results