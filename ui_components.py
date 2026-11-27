"""ui_components.py - small HTML/CSS helpers and Streamlit panels for the ATS / portfolio features.

Keeps app.py lean: app.py only calls the render_* functions below.
Pill/badge classes (.dc-pill, .dc-card, ...) are styled by the CSS block in app.py.
"""

from __future__ import annotations

import re
from html import escape

import streamlit as st

import ats_engine as ats
from ai_tutor import stream_ai_tutor
from portfolio_builder import build_readme

# --------------------------------------------------------------------------- #
# Pill / badge helpers (pure HTML strings)
# --------------------------------------------------------------------------- #
_LEVEL_TONES = {0: "muted", 1: "info", 2: "mid", 3: "high"}
_DIFFICULTY_TONES = {"beginner": "info", "intermediate": "mid", "advanced": "high"}


def pill(text: str, tone: str = "muted", icon: str = "") -> str:
    """Return a styled pill. tone: muted | info | mid | high | low | accent."""
    icon_html = f'<span class="dc-pill-ico">{escape(icon)}</span>' if icon else ""
    return f'<span class="dc-pill dc-{escape(tone)}">{icon_html}{escape(str(text))}</span>'


def level_pill(level: int) -> str:
    level = max(0, min(3, int(level)))
    return pill(ats.LEVEL_LABELS[level], _LEVEL_TONES[level])


def difficulty_pill(label: str) -> str:
    """Accepts 'Beginner' / 'Intermediate' / 'Advanced' or a title such as '1. [Beginner] Revenue ...'."""
    match = re.search(r"\[(Beginner|Intermediate|Advanced)\]", label or "", flags=re.I) or re.search(
        r"\b(Beginner|Intermediate|Advanced)\b", label or "", flags=re.I
    )
    if not match:
        return ""
    word = match.group(1).capitalize()
    return pill(word, _DIFFICULTY_TONES[word.lower()])


def ats_pill(score: int) -> str:
    tone = ats.score_tone(score)
    return pill(f"ATS match {score}%", tone, icon="●")


def pills_row(*pills: str) -> str:
    return '<div class="dc-pill-row">' + "".join(p for p in pills if p) + "</div>"


def show_html(html: str) -> None:
    # Markdown turns 4+ space-indented lines into code blocks, so flatten the HTML to one line.
    flat = "".join(line.strip() for line in html.splitlines())
    st.markdown(flat, unsafe_allow_html=True)


def module_title_map(curriculum) -> dict[str, str]:
    """{module_id: title} from curriculum.json (nested-dict layout); tolerant of other layouts."""
    titles: dict[str, str] = {}
    try:
        groups = curriculum.values() if isinstance(curriculum, dict) else curriculum
        for group in groups:
            levels = group.values() if isinstance(group, dict) else group if isinstance(group, list) else []
            for mod in levels:
                if isinstance(mod, dict) and mod.get("module_id"):
                    titles[mod["module_id"]] = mod.get("title") or mod["module_id"]
    except Exception:
        pass
    return titles


def skill_level_strip(skills: dict) -> str:
    """Compact pills of the sidebar calibration."""
    return pills_row(*[pill(f"{k}: {ats.LEVEL_LABELS[int(v)]}", _LEVEL_TONES[int(v)]) for k, v in skills.items()])


# --------------------------------------------------------------------------- #
# Interview readiness scorecard
# --------------------------------------------------------------------------- #
def render_readiness_scorecard(cards: list[dict]) -> None:
    html = ['<div class="dc-score-grid">']
    for c in cards:
        nxt = f'<div class="dc-score-next">Next: {escape(c["next"])}</div>' if c["next"] else ""
        html.append(
            f"""
            <div class="dc-card dc-score-card">
              <div class="dc-score-head">
                <span class="dc-score-title">{escape(c["label"])}</span>
                {pill(c["stage"], c["tone"])}
              </div>
              <div class="dc-score-pct">{c["pct"]}<span>%</span></div>
              <div class="dc-bar"><div class="dc-bar-fill dc-fill-{c["tone"]}" style="width:{c["pct"]}%"></div></div>
              <div class="dc-score-meta">{c["done"]}/{c["total"]} {escape(c["unit"])} · {level_pill(c["level"])}</div>
              <div class="dc-score-focus">{escape(c["focus"])}</div>
              {nxt}
            </div>"""
        )
    html.append("</div>")
    show_html("".join(html))


# --------------------------------------------------------------------------- #
# JD keyword & skill-gap analyzer
# --------------------------------------------------------------------------- #
def _load_sample_jd() -> None:
    st.session_state["jd_text"] = ats.SAMPLE_JD


def _keyword_chip(item: dict) -> str:
    tone = {"covered": "high", "gap": "low", "outside": "muted"}[item["status"]]
    icon = {"covered": "✓", "gap": "✕", "outside": "•"}[item["status"]]
    tip = escape(item.get("need", ""), quote=True)
    badge = ""
    if item["priority"] == "Must-have":
        badge = ' <span class="dc-chip-tag">must</span>'
    elif item["priority"] == "Nice-to-have":
        badge = ' <span class="dc-chip-tag">nice</span>'
    return f'<span class="dc-pill dc-{tone}" title="{tip}"><span class="dc-pill-ico">{icon}</span>{escape(item["name"])}{badge}</span>'


def render_jd_analyzer(
    skills: dict,
    completed_ids,
    curriculum,
    projects: list[dict],
    selected_proj: dict,
    gemini_key: str,
) -> None:
    st.markdown("#### JD Keyword & Skill Gap Analyzer")
    st.caption(
        "Paste a Data Analyst job description. Keywords are matched deterministically against your calibrated "
        "skills, completed modules and portfolio progress - no AI call needed."
    )

    st.text_area(
        "Job description",
        key="jd_text",
        height=200,
        placeholder="Paste the full Data Analyst job description here...",
        label_visibility="collapsed",
    )
    st.button("Load sample JD", key="btn_jd_sample", on_click=_load_sample_jd)

    jd_text = st.session_state.get("jd_text", "") or ""
    if not jd_text.strip():
        st.info("Paste a JD (or load the sample) to see matched keywords, missing ATS keywords and tailored bullets.")
        return

    done_steps, _ = ats.portfolio_progress(st.session_state, projects)
    analysis = ats.analyze_jd(
        jd_text,
        skills,
        completed_ids,
        portfolio_steps_done=done_steps,
        module_titles=module_title_map(curriculum),
    )

    if not analysis["keywords"]:
        st.warning("No recognizable analytics keywords found. Make sure you pasted the full job description.")
        return

    show_html(
        pills_row(
            ats_pill(analysis["ats_score"]),
            pill(f'{len(analysis["matched"])} covered', "high"),
            pill(f'{len(analysis["gaps"])} learnable gaps', "low"),
            pill(f'{len(analysis["outside"])} outside roadmap', "muted"),
            pill(f'{analysis["word_count"]} words', "info"),
        )
    )

    chips = "".join(_keyword_chip(k) for k in analysis["keywords"])
    show_html(f'<div class="dc-card"><div class="dc-card-title">Top JD keywords</div><div class="dc-chip-wrap">{chips}</div>'
              '<div class="dc-legend">✓ you can show it · ✕ missing · • outside this roadmap (mention only if true)</div></div>')

    if analysis["gaps"]:
        st.markdown("##### Missing ATS keywords - how to close each")
        for g in analysis["gaps"]:
            action = f"reach **{g['need']}**"
            if g["module_title"]:
                action += f" via module *{g['module_title']}*"
            st.markdown(f"- **{g['name']}** ({g['priority']}) - {action}. You are at **{g['you_have']}**.")
    else:
        st.success("You cover every roadmap keyword in this JD. Mirror the exact phrases on your resume.")

    if analysis["outside"]:
        st.caption(
            "Outside the DA Coach roadmap: " + ", ".join(o["name"] for o in analysis["outside"])
            + ". Add these only where you have genuinely used them (course project, certificate, side project)."
        )

    st.markdown("##### 2 tailored resume bullets")
    bullets = ats.suggest_gap_bullets(analysis, selected_proj["id"], n=2)
    if bullets:
        for b in bullets:
            tag = "closes gap" if b["mode"] == "gap" else "reinforces strength"
            show_html(pills_row(pill(tag, "low" if b["mode"] == "gap" else "high"), *[pill(k, "muted") for k in b["keywords"]]))
            st.markdown(f"- {b['text']}")
        st.code("\n".join(f"• {b['text']}" for b in bullets), language="text")
        st.caption(f"Contextualized for **{selected_proj['title']}**. Replace [brackets] with real numbers before using.")
    else:
        st.caption("No bullet suggestions for this JD yet.")

    # --- Optional AI deep audit (existing streaming tutor, unchanged) ---
    fp = ats.jd_fingerprint(jd_text)
    ai_clicked = st.button("AI Deep JD Audit", key="btn_jd_ai_audit", use_container_width=True)
    if ai_clicked:
        prompt = ats.build_jd_audit_prompt(jd_text, analysis, skills, selected_proj["title"])
        text = st.write_stream(stream_ai_tutor(prompt, gemini_key))
        st.session_state["jd_ai_audit"] = {"fp": fp, "text": text if isinstance(text, str) else ""}
    else:
        saved = st.session_state.get("jd_ai_audit")
        if saved and saved.get("fp") == fp and saved.get("text"):
            with st.expander("Last AI Deep JD Audit", expanded=True):
                st.markdown(saved["text"])


# --------------------------------------------------------------------------- #
# README / case-study generator
# --------------------------------------------------------------------------- #
def render_readme_generator(project: dict, skills: dict) -> None:
    st.markdown("#### GitHub README.md & Case Study Generator")
    st.caption("One click gives a recruiter-grade README for the selected project, filled with the metrics you entered in the Resume Bullet Builder.")

    pid = project["id"]
    author = st.text_input("Your name (optional)", key="readme_author", placeholder="e.g., Asha Verma")

    out_key = f"readme_md_{pid}"
    if st.button("Generate README.md", type="primary", key=f"btn_readme_{pid}", use_container_width=True):
        metrics = {
            "rows": st.session_state.get(f"m_vol_{pid}", ""),
            "pct": st.session_state.get(f"m_pct_{pid}", ""),
            "scope": st.session_state.get(f"m_seg_{pid}", ""),
        }
        strong = [f"{k} ({ats.LEVEL_LABELS[int(v)]})" for k, v in skills.items() if int(v) >= 1]
        st.session_state[out_key] = build_readme(project, metrics, author=author, skills_line=", ".join(strong))

    readme_md = st.session_state.get(out_key)
    if not readme_md:
        st.info(f"Click **Generate README.md** to build the case study for *{project['title']}*.")
        return

    st.download_button(
        "Download README.md",
        data=readme_md,
        file_name="README.md",
        mime="text/markdown",
        key=f"dl_readme_{pid}",
        use_container_width=True,
    )
    st.caption("Copy with the icon at the top-right of the block, then paste into your repo's README.md.")
    st.code(readme_md, language="markdown")
    with st.expander("Rendered preview"):
        st.markdown(readme_md)