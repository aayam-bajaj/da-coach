from portfolio_builder import PORTFOLIO_PROJECTS, build_resume_bullets
import ats_engine as ats
from ui_components import (
    difficulty_pill,
    level_pill,
    pills_row,
    render_jd_analyzer,
    render_readiness_scorecard,
    render_readme_generator,
    show_html,
    skill_level_strip,
)
import json
from datetime import date
from urllib.parse import quote_plus
import streamlit as st

from progress_store import (
    export_progress_json,
    get_completed_set,
    get_conn,
    get_streak_and_hours,
    import_progress_json,
    log_study_session,
    toggle_module_status,
)
from youtube_curator import fetch_top_youtube_resources
from sql_sandbox import SQL_CHALLENGES, execute_and_grade, get_expected_preview
from pandas_sandbox import PANDAS_CHALLENGES, get_messy_orders_df, run_pandas_sandbox
from ai_tutor import stream_ai_tutor

st.set_page_config(
    page_title="DA Coach — Data Analyst Prep",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --dc-bg: #090A0F;
        --dc-panel: rgba(18, 21, 31, 0.72);
        --dc-border: rgba(203, 213, 225, 0.16);
        --dc-border-strong: rgba(226, 232, 240, 0.34);
        --dc-text: #F8FAFC;
        --dc-muted: #94A3B8;
        --dc-chrome: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 35%, #64748B 52%, #F8FAFC 78%, #94A3B8 100%);
        --dc-radius: 13px;
        --dc-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", Menlo, Consolas, monospace;
        --dc-green: #86EFAC;
        --dc-amber: #FCD34D;
        --dc-red: #FCA5A5;
        --dc-blue: #93C5FD;
    }
    .stApp {
        background: radial-gradient(circle at 15% 8%, #1F2430 0%, #090A0F 55%, #050608 100%);
        color: var(--dc-text);
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
        max-width: 1280px;
    }
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }

    /* Typography */
    h1 {
        background: var(--dc-chrome);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.03em;
        margin-bottom: 0.15rem !important;
    }
    h2, h3, h4 { letter-spacing: -0.015em; color: #F8FAFC; }
    h4 { font-weight: 700 !important; }
    [data-testid="stCaptionContainer"] { color: var(--dc-muted); }
    .stApp a { color: #CBD5E1; text-underline-offset: 3px; }

    /* Prevent horizontal overflow inside split panes */
    div[data-testid="stColumn"], div[data-testid="column"] { min-width: 0; }
    div[data-testid="stHorizontalBlock"] { gap: 1.1rem; }
    .stMarkdown, .stMarkdown p, .stMarkdown li { overflow-wrap: anywhere; }

    /* Glass KPI Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 35, 48, 0.72), rgba(12, 14, 21, 0.88));
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--dc-border);
        border-top: 1px solid rgba(255, 255, 255, 0.34);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.10);
        padding: 13px 16px;
        border-radius: var(--dc-radius);
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800;
        letter-spacing: -0.02em;
        font-variant-numeric: tabular-nums;
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--dc-muted);
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
    }

    /* Tabs */
    div[data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; scrollbar-width: none; }
    div[data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    button[data-baseweb="tab"] { white-space: nowrap; font-weight: 600; }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(248, 250, 252, 0.08) !important;
        border-radius: 8px 8px 0 0 !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        background: var(--dc-panel);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--dc-border);
        border-top-color: rgba(255, 255, 255, 0.22);
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.32);
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary:hover { background: rgba(248, 250, 252, 0.04); }

    /* Code editors (SQL / Pandas text areas) */
    div[data-testid="stTextArea"] textarea {
        font-family: var(--dc-mono) !important;
        font-size: 0.88rem;
        line-height: 1.55;
        color: #F1F5F9;
        background: #0B0D14 !important;
        border: 1px solid var(--dc-border-strong) !important;
        border-radius: 10px;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.55);
        tab-size: 4;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #E2E8F0 !important;
        box-shadow: 0 0 0 2px rgba(226, 232, 240, 0.18), inset 0 2px 8px rgba(0, 0, 0, 0.55);
    }
    div[data-testid="stTextInput"] input {
        background: #0B0D14 !important;
        border: 1px solid var(--dc-border) !important;
        border-radius: 10px;
    }
    div[data-testid="stTextInput"] input:focus { border-color: #E2E8F0 !important; }
    div[data-baseweb="select"] > div {
        background: #0B0D14;
        border: 1px solid var(--dc-border);
        border-radius: 10px;
    }

    /* Code blocks, dataframes, alerts */
    div[data-testid="stCode"], div[data-testid="stCodeBlock"] {
        border: 1px solid var(--dc-border);
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stCode"] pre, div[data-testid="stCodeBlock"] pre,
    div[data-testid="stCode"] code, div[data-testid="stCodeBlock"] code {
        font-family: var(--dc-mono) !important;
        font-size: 0.85rem;
        line-height: 1.55;
    }
    div[data-testid="stCode"] pre, div[data-testid="stCodeBlock"] pre { overflow-x: auto; max-width: 100%; }
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        border: 1px solid var(--dc-border);
        border-radius: 10px;
        overflow: auto;
        max-width: 100%;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.30);
    }
    div[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }
    div[data-testid="stAlert"] {
        border: 1px solid var(--dc-border);
        border-radius: 12px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }

    /* Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #F8FAFC 0%, #CBD5E1 50%, #94A3B8 100%) !important;
        color: #090A0F !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 255, 255, 0.85) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 16px rgba(226, 232, 240, 0.18);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.32);
    }
    button[kind="secondary"], div[data-testid="stDownloadButton"] button, a[data-testid="stBaseLinkButton-secondary"] {
        background: rgba(30, 35, 48, 0.55) !important;
        border: 1px solid var(--dc-border-strong) !important;
        border-radius: 10px !important;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    button[kind="secondary"]:hover, div[data-testid="stDownloadButton"] button:hover {
        border-color: #F8FAFC !important;
        background: rgba(248, 250, 252, 0.07) !important;
    }

    /* Sidebar Chrome Rail */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1017 0%, #07080C 100%);
        border-right: 1px solid var(--dc-border);
    }

    /* ---------- Pills / badges (ui_components.py) ---------- */
    .dc-pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 10px; }
    .dc-pill {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 2px 10px; border-radius: 999px;
        font-size: 0.74rem; font-weight: 650; letter-spacing: 0.02em; line-height: 1.6;
        white-space: nowrap;
        color: #E2E8F0; background: rgba(148, 163, 184, 0.12);
        border: 1px solid rgba(148, 163, 184, 0.30);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    .dc-pill-ico { font-size: 0.7rem; opacity: 0.9; }
    .dc-high  { color: var(--dc-green); background: rgba(134, 239, 172, 0.10); border-color: rgba(134, 239, 172, 0.38); }
    .dc-mid   { color: var(--dc-amber); background: rgba(252, 211, 77, 0.10);  border-color: rgba(252, 211, 77, 0.38); }
    .dc-low   { color: var(--dc-red);   background: rgba(252, 165, 165, 0.10); border-color: rgba(252, 165, 165, 0.38); }
    .dc-info  { color: var(--dc-blue);  background: rgba(147, 197, 253, 0.10); border-color: rgba(147, 197, 253, 0.38); }
    .dc-muted { color: #CBD5E1; }
    .dc-chip-tag {
        font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.08em;
        padding: 0 5px; border-radius: 4px; background: rgba(255, 255, 255, 0.10);
    }

    /* ---------- Glass cards, scorecard ---------- */
    .dc-card {
        background: linear-gradient(145deg, rgba(30, 35, 48, 0.62), rgba(12, 14, 21, 0.86));
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--dc-border);
        border-top-color: rgba(255, 255, 255, 0.28);
        border-radius: var(--dc-radius);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.40), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        padding: 14px 16px; margin: 6px 0 12px;
        min-width: 0;
    }
    .dc-card-title { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--dc-muted); margin-bottom: 8px; }
    .dc-chip-wrap { display: flex; flex-wrap: wrap; gap: 7px; }
    .dc-legend { margin-top: 10px; font-size: 0.74rem; color: var(--dc-muted); }

    .dc-score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 4px 0 8px; }
    .dc-score-card { margin: 0; display: flex; flex-direction: column; gap: 8px; }
    .dc-score-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
    .dc-score-title { font-weight: 700; font-size: 0.92rem; }
    .dc-score-pct {
        font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; font-variant-numeric: tabular-nums; line-height: 1;
        background: var(--dc-chrome); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .dc-score-pct span { font-size: 1rem; margin-left: 2px; }
    .dc-bar { height: 7px; border-radius: 999px; background: rgba(148, 163, 184, 0.18); overflow: hidden; }
    .dc-bar-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
    .dc-fill-high { background: linear-gradient(90deg, #4ADE80, #BBF7D0); }
    .dc-fill-mid  { background: linear-gradient(90deg, #FBBF24, #FDE68A); }
    .dc-fill-low  { background: linear-gradient(90deg, #F87171, #FECACA); }
    .dc-score-meta { font-size: 0.78rem; color: var(--dc-muted); display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .dc-score-focus { font-size: 0.78rem; color: #CBD5E1; line-height: 1.45; }
    .dc-score-next { font-size: 0.74rem; color: var(--dc-muted); border-top: 1px solid var(--dc-border); padding-top: 7px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_json(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        return json.loads(data) if isinstance(data, str) else data


try:
    curriculum = load_json("curriculum.json")
    diagnostic_quiz = load_json("diagnostic_quiz.json")
    study_vault = load_json("study_vault.json")
except Exception as e:
    st.error(f"Error loading JSON data files: {e}")
    st.stop()


@st.cache_data
def build_training_queue(raw_curriculum, skills_tuple: tuple):
    skills = dict(skills_tuple)
    queue, skipped = [], []

    if isinstance(raw_curriculum, dict) and isinstance(raw_curriculum.get("tracks"), list):
        iterable_tracks = [
            (t.get("name") or t.get("track") or "Unknown", t.get("levels") or t.get("modules") or [])
            for t in raw_curriculum["tracks"]
        ]
    elif isinstance(raw_curriculum, dict):
        iterable_tracks = list(raw_curriculum.items())
    else:
        iterable_tracks = [
            (t.get("name") or t.get("track") or "Unknown", t.get("levels") or t.get("modules") or [])
            for t in raw_curriculum
        ]

    for track, levels in iterable_tracks:
        if isinstance(levels, str):
            levels = json.loads(levels)
        user_lvl = skills.get(track, 0)
        level_items = levels.items() if isinstance(levels, dict) else enumerate(levels, 1)

        for lvl_key, mod in level_items:
            if isinstance(mod, str):
                mod = json.loads(mod)
            if not isinstance(mod, dict):
                continue

            raw_lvl = str(lvl_key).split(":")[0].strip()
            lvl_num = int(raw_lvl) if raw_lvl.isdigit() else int(str(mod.get("level", 1)).split(":")[0].strip())
            mod_id = mod.get("module_id") or f"{track}_L{lvl_num}"
            title = mod.get("title") or mod.get("name") or f"Level {lvl_num}"
            est_hours = mod.get("estimated_hours") or mod.get("hours") or 5
            topics = mod.get("key_topics") or mod.get("topics") or []
            yt_query = mod.get("youtube_search_query") or f"{track} {title} data analyst tutorial"

            entry = {
                "module_id": mod_id,
                "track": track,
                "level": lvl_num,
                "title": title,
                "estimated_hours": est_hours,
                "key_topics": topics,
                "youtube_search_query": yt_query,
            }
            if lvl_num <= user_lvl:
                skipped.append(f"{track} — {title}")
            else:
                queue.append(entry)

    queue.sort(key=lambda x: x["level"])
    return skipped, queue


conn = get_conn()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🎯 Skill Calibration")
    skills = {
        "Excel": st.slider("Excel", 0, 3, 0, key="sk_excel"),
        "Power BI": st.slider("Power BI / Tableau", 0, 3, 0, key="sk_bi"),
        "SQL": st.slider("SQL", 0, 3, 0, key="sk_sql"),
        "Python": st.slider("Python (Pandas)", 0, 3, 0, key="sk_py"),
        "Stats": st.slider("Business Stats", 0, 3, 0, key="sk_stats"),
    }
    show_html(skill_level_strip(skills))

    st.markdown("### ⏱️ Weekly Schedule")
    hours_per_day = st.selectbox("Hours / day", [1, 2, 3, 4], index=1, key="sched_hpd")
    days_per_week = st.slider("Study days / week", 3, 7, 5, key="sched_dpw")
    weekly_budget = hours_per_day * days_per_week

    st.markdown("### 🤖 AI Tutor Key")
    gemini_key = st.text_input(
        "Gemini API Key (optional if set in Secrets)",
        type="password",
        placeholder="AIza...",
        key="gemini_api_key",
    )

    st.divider()
    streak, total_logged_hrs, history = get_streak_and_hours(conn)
    c1, c2 = st.columns(2)
    c1.metric("Streak", f"{streak}d")
    c2.metric("Logged", f"{total_logged_hrs}h")

    st.divider()
    st.markdown("### 💾 Backup & Restore")
    st.download_button(
        "Export Progress JSON",
        data=export_progress_json(conn),
        file_name="da_coach_progress.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded_backup = st.file_uploader("Restore JSON", type=["json"], label_visibility="collapsed", key="backup_up")
    if uploaded_backup is not None and st.button("Import Backup", use_container_width=True, key="backup_apply"):
        try:
            import_progress_json(conn, uploaded_backup.getvalue().decode("utf-8"))
            st.success("Progress restored.")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid backup file: {e}")


# --- Derived Metrics ---
skipped, queue = build_training_queue(curriculum, tuple(sorted(skills.items())))
completed_ids = get_completed_set(conn)

total_required = len(skipped) + len(queue)
done_count = len(skipped) + sum(1 for m in queue if m["module_id"] in completed_ids)
readiness_pct = int((done_count / total_required) * 100) if total_required else 0
remaining_hrs = sum(m["estimated_hours"] for m in queue if m["module_id"] not in completed_ids)
est_weeks_left = round(remaining_hrs / weekly_budget, 1) if weekly_budget else 0.0
next_mod = next((m for m in queue if m["module_id"] not in completed_ids), None)

# Keep portfolio checklist state alive across reruns / project switches (no st.rerun needed)
ats.sync_portfolio_state(st.session_state, PORTFOLIO_PROJECTS)
portfolio_done, portfolio_target = ats.portfolio_progress(st.session_state, PORTFOLIO_PROJECTS)

# --- Header & KPI Strip ---
st.title("Data Analyst Prep Coach")
st.caption("Calibrated study roadmap • Hands-on SQL & Pandas sandboxes • Cheatsheets & streaming AI coach")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Job Readiness", f"{readiness_pct}%")
k2.metric("Modules Done", f"{done_count}/{total_required}")
k3.metric("Weekly Target", f"{weekly_budget} hrs")
k4.metric("Est. Weeks Left", f"{est_weeks_left}")

st.progress(readiness_pct / 100)

with st.expander("🎯 Interview Readiness Scorecard — what recruiters look for", expanded=False):
    render_readiness_scorecard(
        ats.compute_readiness(skills, queue, skipped, completed_ids, portfolio_done, portfolio_target)
    )

if next_mod:
    st.info(
        f"**Next Up ({hours_per_day}h target):** [{next_mod['track']}] **{next_mod['title']}** "
        f"({next_mod['estimated_hours']}h est.) — watch a curated playlist, drill the topic, and check it off."
    )
else:
    st.success("All queued modules completed for your current skill calibration.")

# --- 4 Clean Primary Modes ---
tab_plan, tab_lab, tab_study, tab_routine, tab_portfolio = st.tabs([
    "🏋️ Workout Plan",
    "💻 Practice Lab",
    "📘 Study & AI Coach",
    "📅 Routine & Check",
    "🚀 Portfolio & Resume",
])

# 1. WORKOUT PLAN
with tab_plan:
    left, right = st.columns([1, 2.3])
    with left:
        st.markdown("#### Skipped (Already Strong)")
        if skipped:
            for s in skipped:
                st.markdown(f"- ✅ {s}")
        else:
            st.caption("No modules skipped at current slider levels.")

    with right:
        st.markdown("#### Active Training Queue")
        if not queue:
            st.success("No remaining modules in queue.")
        for idx, mod in enumerate(queue, 1):
            is_done = mod["module_id"] in completed_ids
            icon = "✅" if is_done else "⬜"
            header = f"{icon} {idx}. [{mod['track']}] {mod['title']} — {mod['estimated_hours']}h"

            with st.expander(header, expanded=(next_mod is not None and mod["module_id"] == next_mod["module_id"])):
                checked = st.checkbox("Mark Module Complete", value=is_done, key=f"chk_{mod['module_id']}")
                if checked != is_done:
                    toggle_module_status(conn, mod["module_id"], checked)
                    st.rerun()

                show_html(pills_row(level_pill(mod["level"])))
                if mod["key_topics"]:
                    st.write("**Key Topics:**", " • ".join(str(t) for t in mod["key_topics"]))

                fallback_url = (
                    f"https://www.youtube.com/results?search_query="
                    f"{quote_plus(mod['youtube_search_query'] + ' playlist')}"
                )
                b1, b2 = st.columns(2)
                fetch_clicked = b1.button("Fetch Top Playlists", key=f"yt_{mod['module_id']}", use_container_width=True)
                b2.link_button("Open YouTube Search", fallback_url, use_container_width=True)

                if fetch_clicked:
                    with st.spinner("Searching YouTube..."):
                        videos = fetch_top_youtube_resources(mod["youtube_search_query"], max_results=3)
                        for v in videos:
                            views_str = f" • {v['views']:,} views" if v.get("views") else ""
                            st.markdown(f"- [{v['title']}]({v['url']}) — *{v['channel']}*{views_str}")
                if st.button("Generate Deep Study Guide", key=f"guide_{mod['module_id']}", use_container_width=True):
                    guide_prompt = (
                        f"Create a structured Data Analyst study guide for: [{mod['track']}] {mod['title']}.\n"
                        f"Key topics: {', '.join(str(t) for t in mod['key_topics'])}.\n"
                        "Include:\n"
                        "1. Core Concept & Business Why (2-3 bullets)\n"
                        "2. Syntax / Formula Cheat Block\n"
                        "3. Common Interview Trap\n"
                        "4. 1 Mini Practice Question with Answer"
                    )
                    st.write_stream(stream_ai_tutor(guide_prompt, gemini_key))

# 2. PRACTICE LAB (SQL + PANDAS SUB-TABS)
with tab_lab:
    sub_sql, sub_pd = st.tabs(["💻 SQL Sandbox", "🐼 Pandas Cleaning Sandbox"])

    with sub_sql:
        col_prompt, col_editor = st.columns([1, 1.35])
        with col_prompt:
            st.markdown("#### Challenge")
            challenge_titles = [c["title"] for c in SQL_CHALLENGES]
            chosen_sql_title = st.selectbox("Select SQL Challenge", challenge_titles, key="sql_sel")
            sql_challenge = next(c for c in SQL_CHALLENGES if c["title"] == chosen_sql_title)
            show_html(pills_row(difficulty_pill(chosen_sql_title)))
            st.info(sql_challenge["prompt"])
            for h_idx, hint_text in enumerate(sql_challenge.get("hints", []), 1):
                with st.expander(f"💡 Progressive Hint {h_idx}"):
                    st.write(hint_text)

            with st.expander("👀 Expected Output Preview"):
                st.dataframe(get_expected_preview(sql_challenge["solution"]), use_container_width=True)

            with st.expander("Database Schema (`customers`, `products`, `orders`)", expanded=True):
                st.code(
                    "customers(customer_id, name, city, segment, signup_date)\n"
                    "products(product_id, product_name, category, unit_price)\n"
                    "orders(order_id, customer_id, product_id, quantity, order_date, status)",
                    language="sql",
                )

        with col_editor:
            st.markdown("#### Query Editor")
            sql_state_key = f"sql_draft_{chosen_sql_title}"
            if sql_state_key not in st.session_state:
                st.session_state[sql_state_key] = ""

            user_sql = st.text_area(
                "SQL Query",
                value=st.session_state[sql_state_key],
                height=165,
                placeholder="SELECT ...",
                key=f"sql_area_{chosen_sql_title}",
                label_visibility="collapsed",
            )
            st.session_state[sql_state_key] = user_sql

            c_run, c_hint = st.columns(2)
            run_sql = c_run.button("Run & Grade SQL", type="primary", use_container_width=True, key="btn_run_sql")
            ai_sql_hint = c_hint.button("AI Hint on Query", use_container_width=True, key="btn_hint_sql")

            if run_sql and user_sql.strip():
                df_out, err, passed = execute_and_grade(user_sql, sql_challenge["solution"])
                if err:
                    st.error(err)
                else:
                    st.dataframe(df_out, use_container_width=True)
                    if passed:
                        st.success("Exact match! Challenge solved.")
                    else:
                        st.warning("Query executed, but rows or values do not match expected output yet.")

            if ai_sql_hint and user_sql.strip():
                review_prompt = (
                    f"SQL Problem: {sql_challenge['prompt']}\n"
                    f"Candidate SQL:\n```sql\n{user_sql}\n```\n"
                    "Give a concise hint on any logic/syntax issue or optimization without revealing the full query."
                )
                st.write_stream(stream_ai_tutor(review_prompt, gemini_key))

    with sub_pd:
        p_col_left, p_col_right = st.columns([1, 1.35])
        with p_col_left:
            st.markdown("#### Cleaning Task")
            p_titles = [c["title"] for c in PANDAS_CHALLENGES]
            chosen_p_title = st.selectbox("Select Pandas Challenge", p_titles, key="pd_sel")
            p_challenge = next(c for c in PANDAS_CHALLENGES if c["title"] == chosen_p_title)
            show_html(pills_row(difficulty_pill(chosen_p_title)))
            st.info(p_challenge["prompt"])
            for h_idx, hint_text in enumerate(p_challenge.get("hints", []), 1):
                with st.expander(f"💡 Progressive Hint {h_idx}"):
                    st.write(hint_text)

            with st.expander("✅ Reference Solution"):
                st.code(p_challenge.get("solution_code", ""), language="python")

            with st.expander("Preview Raw Messy Dataset (`orders`)", expanded=False):
                st.dataframe(get_messy_orders_df(), use_container_width=True)

        with p_col_right:
            st.markdown("#### Pandas Code (`df` Preloaded)")
            pd_state_key = f"pd_draft_{chosen_p_title}"
            if pd_state_key not in st.session_state:
                st.session_state[pd_state_key] = p_challenge["starter_code"]

            user_py = st.text_area(
                "Pandas Code",
                value=st.session_state[pd_state_key],
                height=165,
                key=f"pd_area_{chosen_p_title}",
                label_visibility="collapsed",
            )
            st.session_state[pd_state_key] = user_py

            b_run, b_ai = st.columns(2)
            run_pd = b_run.button("Run & Check Cleaning", type="primary", use_container_width=True, key="btn_run_pd")
            ask_pd_ai = b_ai.button("AI Hint on Pandas", use_container_width=True, key="btn_hint_pd")

            if run_pd and user_py.strip():
                out_df, nulls, err, passed = run_pandas_sandbox(user_py, p_challenge)
                if err:
                    st.error(err)
                else:
                    st.dataframe(out_df, use_container_width=True)
                    st.caption(f"Null counts after run: {nulls}")
                    if passed:
                        st.success(p_challenge["success_msg"])
                    else:
                        st.warning("Code ran, but one or more cleaning requirements are not met yet.")

            if ask_pd_ai and user_py.strip():
                pd_prompt = (
                    f"Pandas cleaning task: {p_challenge['prompt']}\n"
                    f"User code:\n```python\n{user_py}\n```\n"
                    "Give a concise hint on fixing bugs or edge cases without giving away the full answer."
                )
                st.write_stream(stream_ai_tutor(pd_prompt, gemini_key))

# 3. STUDY & AI COACH
with tab_study:
    sub_vault, sub_ai = st.tabs(["📘 Cheatsheets & Drills", "🤖 Live AI Tutor"])

    with sub_vault:
        vault_items = (
            list(study_vault.items())
            if isinstance(study_vault, dict)
            else [(item.get("topic", f"Topic {i + 1}"), item) for i, item in enumerate(study_vault)]
        )
        topic_names = [name for name, _ in vault_items]
        selected_topic = st.selectbox("Select Study Topic", topic_names, key="vault_topic")
        topic_data = dict(vault_items).get(selected_topic, {})

        st.markdown(topic_data.get("cheatsheet_markdown", "No cheatsheet available."))
        st.divider()
        st.markdown("#### Practice Drills")
        for d_idx, drill in enumerate(topic_data.get("drills", []), 1):
            st.markdown(f"**Drill {d_idx}:** {drill.get('prompt')}")
            c_h, c_s = st.columns(2)
            with c_h.expander("Hint"):
                st.write(drill.get("hint", ""))
            with c_s.expander("Solution"):
                st.code(drill.get("solution_code", ""), language="sql")

    with sub_ai:
        st.markdown("#### Ask Your Data Analyst Coach")
        mode = st.radio(
            "Response Mode",
            ["Generate Study Guide", "Explain Concept", "Mock Interview Question"],
            horizontal=True,
            key="ai_mode",
        )
        default_topic = f"{next_mod['track']} — {next_mod['title']}" if next_mod else ""
        topic_input = st.text_input(
            "Topic or Question",
            value=default_topic,
            placeholder="e.g., Window functions vs GROUP BY, or explain p-value in A/B testing",
            key="ai_topic_input",
        )
        if st.button("Ask Coach", type="primary", key="btn_ask_coach") and topic_input.strip():
            weak_skills = [k for k, v in skills.items() if v == 0]
            full_prompt = f"Mode: {mode} | Unstarted tracks: {weak_skills} | Request: {topic_input.strip()}"
            st.write_stream(stream_ai_tutor(full_prompt, gemini_key))

# 4. ROUTINE & SKILL CHECK
with tab_routine:
    sub_log, sub_diag = st.tabs(["📅 Daily Study Log", "🧪 Skill Verification Gate"])

    with sub_log:
        col_form, col_hist = st.columns([1.2, 1])
        with col_form:
            st.markdown("#### Log Today's Session")
            with st.form("daily_log_form"):
                c_d, c_h = st.columns(2)
                log_day = c_d.date_input("Date", value=date.today())
                hrs = c_h.number_input("Hours studied", min_value=0.5, max_value=12.0, value=float(hours_per_day), step=0.5)
                notes = st.text_input("Session notes", placeholder="e.g., Completed SQL Joins + 2 drills")
                saved = st.form_submit_button("Save Session", type="primary", use_container_width=True)

            if saved:
                log_study_session(conn, log_day.isoformat(), hrs, notes)
                st.success("Session saved.")
                st.rerun()

        with col_hist:
            st.markdown("#### Recent Sessions")
            if history:
                for dt_str, h, n in history[:8]:
                    note_part = f" — {n}" if n else ""
                    st.markdown(f"- **{dt_str}**: {h}h{note_part}")
            else:
                st.caption("No study sessions logged yet.")

    with sub_diag:
        claimed_strong = [k for k, v in skills.items() if v >= 2]
        if not claimed_strong:
            st.info("Slide any skill to Level 2 or 3 in the sidebar to verify your strength before skipping modules.")
        else:
            q_list = diagnostic_quiz if isinstance(diagnostic_quiz, list) else diagnostic_quiz.get("questions", [])
            relevant_qs = [q for q in q_list if q.get("track") in claimed_strong]
            st.markdown(f"#### Max-Rep Check: {', '.join(claimed_strong)}")

            if not relevant_qs:
                st.caption("No diagnostic questions found for the selected tracks.")
            else:
                with st.form("diag_form"):
                    answers = {}
                    for i, q in enumerate(relevant_qs):
                        st.markdown(f"**{i + 1}. [{q.get('track')}] {q.get('question')}**")
                        answers[i] = st.radio(
                            f"q_{i}",
                            q.get("options", []),
                            key=f"diag_{i}",
                            label_visibility="collapsed",
                        )
                    submit_diag = st.form_submit_button("Check Score", type="primary")

                if submit_diag:
                    score = sum(1 for i, q in enumerate(relevant_qs) if answers.get(i) == q.get("answer"))
                    for i, q in enumerate(relevant_qs):
                        if answers.get(i) != q.get("answer"):
                            st.warning(f"Q{i + 1} [{q.get('track')}]: {q.get('explanation')}")
                    pct = round((score / len(relevant_qs)) * 100)
                    if pct >= 80:
                        st.success(f"Passed ({pct}%) — skipped modules stay unlocked.")
                    else:
                        st.error(f"Scored {pct}% — consider dropping that slider by 1 level.")

# 5. PORTFOLIO PROJECT & RESUME BULLET BUILDER
with tab_portfolio:
    st.subheader("Guided Portfolio Projects & ATS Resume Bullets")
    st.caption("Pick one scoped project per skill gap, ship a clean GitHub repo, and tailor metric-backed bullets.")

    proj_titles = [f"{p['title']} ({p['est_days']})" for p in PORTFOLIO_PROJECTS]
    chosen_proj_label = st.selectbox("Select a Project Blueprint", proj_titles, key="proj_sel")
    selected_proj = PORTFOLIO_PROJECTS[proj_titles.index(chosen_proj_label)]

    sub_proj, sub_jd, sub_readme = st.tabs(["🧱 Project & Resume Bullets", "🔎 JD Gap Analyzer", "📄 README Generator"])

    with sub_proj:
        p_left, p_right = st.columns([1.15, 1])

        with p_left:
            st.markdown(f"#### {selected_proj['title']}")
            st.write("**Stack:**", " • ".join(selected_proj["stack"]), f"| **Level:** {selected_proj['difficulty']}")
            st.info(f"**Business Problem:** {selected_proj['business_problem']}")
            st.write("**Suggested Dataset:**", selected_proj["dataset_idea"])

            st.markdown("##### Step-by-Step Execution Checklist")
            for s_idx, step_text in enumerate(selected_proj["steps"], 1):
                st.checkbox(f"{s_idx}. {step_text}", key=f"pstep_{selected_proj['id']}_{s_idx}")

        with p_right:
            st.markdown("#### Resume Bullet Builder")
            st.caption("Fill in real numbers from your project (or keep brackets as reminders until measured).")

            m1, m2 = st.columns(2)
            vol_val = m1.text_input("Rows / Records", value="25,000+", key=f"m_vol_{selected_proj['id']}")
            pct_val = m2.text_input("Key % / Metric", value="14%", key=f"m_pct_{selected_proj['id']}")
            seg_val = st.text_input("Scope (Categories / Months / Tools)", value="6 categories & 12 months", key=f"m_seg_{selected_proj['id']}")

            bullets = build_resume_bullets(
                selected_proj,
                {
                    "X,000+": vol_val,
                    "X%": pct_val,
                    "X": seg_val,
                    "one-time, repeat, and high-value": seg_val,
                    "Power BI / Excel": "Power BI",
                    "SQL / Python Pandas": "SQL and Python (Pandas)",
                },
            )

            st.markdown("##### Draft Resume Bullets")
            for b in bullets:
                st.markdown(f"- {b}")

            st.code("\n".join(f"• {b}" for b in bullets), language="text")

            if st.button("Polish Bullets with AI Tutor", key=f"btn_polish_{selected_proj['id']}", use_container_width=True):
                polish_prompt = (
                    f"Rewrite these Data Analyst fresher resume bullets to be punchy, action-verb-led, and ATS-friendly "
                    f"for project '{selected_proj['title']}' ({', '.join(selected_proj['stack'])}):\n"
                    + "\n".join(f"- {b}" for b in bullets)
                    + "\nProvide 3 tightened bullets plus 1 quick interview talking point."
                )
                st.write_stream(stream_ai_tutor(polish_prompt, gemini_key))

    with sub_jd:
        render_jd_analyzer(
            skills,
            completed_ids,
            curriculum,
            PORTFOLIO_PROJECTS,
            selected_proj,
            gemini_key,
        )

    with sub_readme:
        render_readme_generator(selected_proj, skills)