import json
from datetime import date
from urllib.parse import quote_plus
import pandas as pd
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
from sql_sandbox import SQL_CHALLENGES, execute_and_grade, init_sandbox_db

try:
    from sql_sandbox import get_expected_preview
except ImportError:
    def get_expected_preview(solution_sql: str) -> pd.DataFrame:
        conn_tmp = init_sandbox_db()
        try:
            return pd.read_sql_query(solution_sql.strip().rstrip(";"), conn_tmp)
        finally:
            conn_tmp.close()

from pandas_sandbox import PANDAS_CHALLENGES, get_messy_orders_df, run_pandas_sandbox
from portfolio_builder import PORTFOLIO_PROJECTS, build_resume_bullets
from ats_engine import analyze_jd_match, compute_track_scorecard, generate_project_readme
from ai_tutor import stream_ai_tutor

st.set_page_config(
    page_title="DA STUDIO // ANALYTICS WORKBENCH",
    page_icon="◼",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap');

    /* Architectural Obsidian Base */
    .stApp {
        background-color: #09090B;
        color: #FAFAFA;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1360px;
    }

    /* Bold Editorial Header */
    h1 {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 900 !important;
        font-size: 2.35rem !important;
        letter-spacing: -0.045em !important;
        line-height: 1.1 !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3, h4 {
        color: #F4F4F5 !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }

    /* Hairline Architectural KPI Cards */
    div[data-testid="stMetric"] {
        background-color: #111114;
        border: 1px solid #27272A;
        border-top: 2px solid #E4E4E7;
        padding: 16px 20px;
        border-radius: 6px;
        box-shadow: none;
    }
    div[data-testid="stMetricLabel"] {
        color: #A1A1AA !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
    }

    /* Sharp Progress Bar */
    div[data-testid="stProgress"] > div > div {
        background-color: #27272A !important;
        height: 6px !important;
        border-radius: 2px !important;
    }
    div[data-testid="stProgress"] > div > div > div {
        background-color: #FAFAFA !important;
        border-radius: 2px !important;
    }

    /* Precision Navigation Tabs */
    div[data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 1px solid #27272A;
        margin-bottom: 1rem;
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #71717A !important;
        border-radius: 0px !important;
        padding: 10px 18px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        border-bottom: 2px solid transparent !important;
        transition: color 0.12s ease, border-color 0.12s ease;
    }
    button[data-baseweb="tab"]:hover {
        color: #E4E4E7 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #FFFFFF !important;
    }

    /* Crisp Expanders & Containers */
    div[data-testid="stExpander"] {
        background-color: #111114;
        border: 1px solid #27272A;
        border-radius: 6px;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #F4F4F5 !important;
    }

    /* Code Editors & Inputs */
    textarea, input, select {
        background-color: #0D0D10 !important;
        border: 1px solid #27272A !important;
        color: #FAFAFA !important;
        border-radius: 6px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.86rem !important;
    }
    textarea:focus, input:focus {
        border-color: #A1A1AA !important;
        box-shadow: none !important;
    }

    /* High-Contrast Tactile Primary Button */
    button[kind="primary"] {
        background-color: #FAFAFA !important;
        color: #09090B !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
        letter-spacing: -0.01em !important;
        border: 1px solid #FAFAFA !important;
        border-radius: 6px !important;
        padding: 0.45rem 1rem !important;
        box-shadow: none !important;
        transition: background-color 0.12s ease;
    }
    button[kind="primary"]:hover {
        background-color: #D4D4D8 !important;
        border-color: #D4D4D8 !important;
    }

    /* Secondary Buttons */
    button[kind="secondary"] {
        background-color: #141417 !important;
        color: #E4E4E7 !important;
        border: 1px solid #27272A !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    button[kind="secondary"]:hover {
        border-color: #52525B !important;
        color: #FFFFFF !important;
    }

    /* Sidebar Architectural Rail */
    section[data-testid="stSidebar"] {
        background-color: #0C0C0E;
        border-right: 1px solid #27272A;
    }
    section[data-testid="stSidebar"] h3 {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.76rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: #A1A1AA !important;
        margin-top: 0.5rem !important;
    }

    /* Industrial Monospace Tags */
    .spec-tag {
        display: inline-block;
        padding: 3px 8px;
        margin: 2px 5px 2px 0;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        background-color: #18181B;
        border: 1px solid #3F3F46;
        color: #E4E4E7;
    }
    .spec-tag-ok {
        background-color: rgba(16, 185, 129, 0.10);
        border-color: #10B981;
        color: #6EE7B7;
    }
    .spec-tag-gap {
        background-color: rgba(245, 158, 11, 0.10);
        border-color: #F59E0B;
        color: #FCD34D;
    }

    /* Scorecard Grid Cells */
    .scorecard-cell {
        background-color: #111114;
        border: 1px solid #27272A;
        border-radius: 6px;
        padding: 14px 16px;
    }
    .scorecard-cell-ready {
        border-left: 3px solid #10B981;
    }
    .scorecard-cell-progress {
        border-left: 3px solid #E4E4E7;
    }
    .scorecard-cell-gap {
        border-left: 3px solid #F59E0B;
    }

    /* Clean Next-Up Dispatch Bar */
    .dispatch-bar {
        background-color: #111114;
        border: 1px solid #27272A;
        border-left: 3px solid #FAFAFA;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 10px 0 18px 0;
        font-size: 0.92rem;
        color: #E4E4E7;
    }
    .dispatch-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #A1A1AA;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_tags(items: list[str], variant: str = "default") -> str:
    cls = "spec-tag"
    if variant == "ok":
        cls += " spec-tag-ok"
    elif variant == "gap":
        cls += " spec-tag-gap"
    return "".join(f'<span class="{cls}">{item}</span>' for item in items)


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
    st.markdown("### 01 // Skill Calibration")
    skills = {
        "Excel": st.slider("Excel", 0, 3, 3, key="sk_excel"),
        "Power BI": st.slider("Power BI / Tableau", 0, 3, 3, key="sk_bi"),
        "SQL": st.slider("SQL", 0, 3, 0, key="sk_sql"),
        "Python": st.slider("Python (Pandas)", 0, 3, 0, key="sk_py"),
        "Stats": st.slider("Business Stats", 0, 3, 0, key="sk_stats"),
    }

    st.markdown("### 02 // Weekly Cadence")
    hours_per_day = st.selectbox("Hours / day", [1, 2, 3, 4], index=1, key="sched_hpd")
    days_per_week = st.slider("Study days / week", 3, 7, 5, key="sched_dpw")
    weekly_budget = hours_per_day * days_per_week

    st.markdown("### 03 // AI Engine Key")
    gemini_key = st.text_input(
        "Gemini API Key (optional if set in Secrets)",
        type="password",
        placeholder="AIza...",
        key="gemini_api_key",
    )

    st.divider()
    streak, total_logged_hrs, history = get_streak_and_hours(conn)
    c1, c2 = st.columns(2)
    c1.metric("STREAK", f"{streak}D")
    c2.metric("LOGGED", f"{total_logged_hrs}H")

    st.divider()
    st.markdown("### 04 // State Backup")
    st.download_button(
        "Export JSON Snapshot",
        data=export_progress_json(conn),
        file_name="da_coach_progress.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded_backup = st.file_uploader("Restore JSON", type=["json"], label_visibility="collapsed", key="backup_up")
    if uploaded_backup is not None and st.button("Apply Snapshot", use_container_width=True, key="backup_apply"):
        try:
            import_progress_json(conn, uploaded_backup.getvalue().decode("utf-8"))
            st.success("State restored.")
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

# --- Header & KPI Strip ---
st.markdown(
    '<div style="font-family:\'JetBrains Mono\',monospace; font-size:0.74rem; color:#A1A1AA; '
    'letter-spacing:0.12em; text-transform:uppercase; margin-bottom:4px;">'
    'DATA ANALYST WORKBENCH // V3.0</div>',
    unsafe_allow_html=True,
)
st.title("Data Analyst Prep Studio")
st.markdown(
    '<div style="color:#A1A1AA; font-size:0.95rem; margin-bottom:16px;">'
    'Calibrated curriculum execution, live SQL/Pandas sandboxes, and ATS job-description alignment.'
    '</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("READINESS", f"{readiness_pct}%")
k2.metric("COMPLETED", f"{done_count}/{total_required}")
k3.metric("WEEKLY BUDGET", f"{weekly_budget} HRS")
k4.metric("EST. RUNWAY", f"{est_weeks_left} WKS")

st.progress(readiness_pct / 100)

if next_mod:
    st.markdown(
        f'<div class="dispatch-bar">'
        f'<span class="dispatch-label">NEXT PRIORITY // {hours_per_day}H BLOCK</span>'
        f'<strong>[{next_mod["track"]}] {next_mod["title"]}</strong> '
        f'<span style="color:#A1A1AA;">({next_mod["estimated_hours"]}h est.)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.success("All queued modules completed for your current skill calibration.")

# --- 5 Clean Primary Modes ---
tab_plan, tab_lab, tab_study, tab_routine, tab_portfolio = st.tabs([
    "01 · ROADMAP",
    "02 · SQL & PANDAS LAB",
    "03 · STUDY VAULT & AI",
    "04 · LOG & SKILL GATE",
    "05 · PORTFOLIO & ATS",
])

# 1. ROADMAP + INTERVIEW READINESS SCORECARD
with tab_plan:
    st.markdown("#### Track Readiness Matrix")
    scorecard = compute_track_scorecard(skills, queue, skipped, completed_ids)
    sc_cols = st.columns(len(scorecard))
    for col, item in zip(sc_cols, scorecard):
        if item["pct"] >= 80:
            variant, cell_cls = "ok", "scorecard-cell scorecard-cell-ready"
        elif item["pct"] >= 35:
            variant, cell_cls = "default", "scorecard-cell scorecard-cell-progress"
        else:
            variant, cell_cls = "gap", "scorecard-cell scorecard-cell-gap"

        with col:
            st.markdown(
                f"""
                <div class="{cell_cls}">
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#A1A1AA; text-transform:uppercase; letter-spacing:0.06em;">{item['track']}</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:1.55rem; font-weight:700; color:#FFFFFF; margin:4px 0 8px 0;">{item['pct']}%</div>
                    {render_tags([item['status']], variant=variant)}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    left, right = st.columns([1, 2.35])
    with left:
        st.markdown("#### Cleared Baseline")
        if skipped:
            for s in skipped:
                st.markdown(f"- **`DONE`** {s}")
        else:
            st.caption("No modules bypassed at current slider levels.")

    with right:
        st.markdown("#### Execution Queue")
        if not queue:
            st.success("Queue clear.")
        for idx, mod in enumerate(queue, 1):
            is_done = mod["module_id"] in completed_ids
            state_badge = "[DONE]" if is_done else "[OPEN]"
            header = f"{state_badge}  {idx:02d}. {mod['track']} — {mod['title']} ({mod['estimated_hours']}h)"

            with st.expander(header, expanded=(next_mod is not None and mod["module_id"] == next_mod["module_id"])):
                checked = st.checkbox("Mark Module Complete", value=is_done, key=f"chk_{mod['module_id']}")
                if checked != is_done:
                    toggle_module_status(conn, mod["module_id"], checked)
                    st.rerun()

                if mod["key_topics"]:
                    st.markdown(
                        render_tags([str(t) for t in mod["key_topics"]]),
                        unsafe_allow_html=True,
                    )

                fallback_url = (
                    f"https://www.youtube.com/results?search_query="
                    f"{quote_plus(mod['youtube_search_query'] + ' playlist')}"
                )
                b1, b2, b3 = st.columns(3)
                fetch_clicked = b1.button("Fetch Top Playlists", key=f"yt_{mod['module_id']}", use_container_width=True)
                b2.link_button("YouTube Search", fallback_url, use_container_width=True)
                guide_clicked = b3.button("Generate Study Guide", key=f"guide_{mod['module_id']}", use_container_width=True)

                if fetch_clicked:
                    with st.spinner("Querying playlists..."):
                        videos = fetch_top_youtube_resources(mod["youtube_search_query"], max_results=3)
                        for v in videos:
                            views_str = f" · {v['views']:,} views" if v.get("views") else ""
                            st.markdown(f"- [{v['title']}]({v['url']}) — *{v['channel']}*{views_str}")

                if guide_clicked:
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
    sub_sql, sub_pd = st.tabs(["SQLITE SANDBOX", "PANDAS CLEANING LAB"])

    with sub_sql:
        col_prompt, col_editor = st.columns([1, 1.35])
        with col_prompt:
            st.markdown("#### Specification")
            challenge_titles = [c["title"] for c in SQL_CHALLENGES]
            chosen_sql_title = st.selectbox("Select SQL Challenge", challenge_titles, key="sql_sel")
            sql_challenge = next(c for c in SQL_CHALLENGES if c["title"] == chosen_sql_title)
            st.info(sql_challenge["prompt"])

            for h_idx, hint_text in enumerate(sql_challenge.get("hints", []), 1):
                with st.expander(f"Hint 0{h_idx}"):
                    st.write(hint_text)

            with st.expander("Expected Output Schema & Rows"):
                st.dataframe(get_expected_preview(sql_challenge["solution"]), use_container_width=True)

            with st.expander("Database Tables (`customers`, `products`, `orders`)", expanded=False):
                st.code(
                    "customers(customer_id, name, city, segment, signup_date)\n"
                    "products(product_id, product_name, category, unit_price)\n"
                    "orders(order_id, customer_id, product_id, quantity, order_date, status)",
                    language="sql",
                )

        with col_editor:
            st.markdown("#### Query Console")
            sql_state_key = f"sql_draft_{chosen_sql_title}"
            if sql_state_key not in st.session_state:
                st.session_state[sql_state_key] = ""

            user_sql = st.text_area(
                "SQL Query",
                value=st.session_state[sql_state_key],
                height=190,
                placeholder="SELECT ...",
                key=f"sql_area_{chosen_sql_title}",
                label_visibility="collapsed",
            )
            st.session_state[sql_state_key] = user_sql

            c_run, c_hint = st.columns(2)
            run_sql = c_run.button("Execute & Validate", type="primary", use_container_width=True, key="btn_run_sql")
            ai_sql_hint = c_hint.button("AI Code Review", use_container_width=True, key="btn_hint_sql")

            if run_sql and user_sql.strip():
                df_out, err, passed = execute_and_grade(user_sql, sql_challenge["solution"])
                if err:
                    st.error(err)
                else:
                    st.dataframe(df_out, use_container_width=True)
                    if passed:
                        st.success("PASS // Exact output match.")
                    else:
                        st.warning("MISMATCH // Query ran, but rows or values differ from expected output.")

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
            st.markdown("#### Specification")
            p_titles = [c["title"] for c in PANDAS_CHALLENGES]
            chosen_p_title = st.selectbox("Select Pandas Challenge", p_titles, key="pd_sel")
            p_challenge = next(c for c in PANDAS_CHALLENGES if c["title"] == chosen_p_title)
            st.info(p_challenge["prompt"])

            for h_idx, hint_text in enumerate(p_challenge.get("hints", []), 1):
                with st.expander(f"Hint 0{h_idx}"):
                    st.write(hint_text)

            with st.expander("Reference Implementation"):
                st.code(p_challenge.get("solution_code", ""), language="python")

            with st.expander("Raw Input Dataset (`orders`)", expanded=False):
                st.dataframe(get_messy_orders_df(), use_container_width=True)

        with p_col_right:
            st.markdown("#### Python Console (`df` Preloaded)")
            pd_state_key = f"pd_draft_{chosen_p_title}"
            if pd_state_key not in st.session_state:
                st.session_state[pd_state_key] = p_challenge["starter_code"]

            user_py = st.text_area(
                "Pandas Code",
                value=st.session_state[pd_state_key],
                height=190,
                key=f"pd_area_{chosen_p_title}",
                label_visibility="collapsed",
            )
            st.session_state[pd_state_key] = user_py

            b_run, b_ai = st.columns(2)
            run_pd = b_run.button("Run & Validate", type="primary", use_container_width=True, key="btn_run_pd")
            ask_pd_ai = b_ai.button("AI Code Review", use_container_width=True, key="btn_hint_pd")

            if run_pd and user_py.strip():
                out_df, nulls, err, passed = run_pandas_sandbox(user_py, p_challenge)
                if err:
                    st.error(err)
                else:
                    st.dataframe(out_df, use_container_width=True)
                    st.caption(f"Null audit: {nulls}")
                    if passed:
                        st.success(f"PASS // {p_challenge['success_msg']}")
                    else:
                        st.warning("MISMATCH // One or more cleaning assertions failed.")

            if ask_pd_ai and user_py.strip():
                pd_prompt = (
                    f"Pandas cleaning task: {p_challenge['prompt']}\n"
                    f"User code:\n```python\n{user_py}\n```\n"
                    "Give a concise hint on fixing bugs or edge cases without giving away the full answer."
                )
                st.write_stream(stream_ai_tutor(pd_prompt, gemini_key))

# 3. STUDY & AI COACH
with tab_study:
    sub_vault, sub_ai = st.tabs(["REFERENCE VAULT", "AI INTERVIEW COACH"])

    with sub_vault:
        vault_items = (
            list(study_vault.items())
            if isinstance(study_vault, dict)
            else [(item.get("topic", f"Topic {i + 1}"), item) for i, item in enumerate(study_vault)]
        )
        topic_names = [name for name, _ in vault_items]
        selected_topic = st.selectbox("Select Reference Topic", topic_names, key="vault_topic")
        topic_data = dict(vault_items).get(selected_topic, {})

        st.markdown(topic_data.get("cheatsheet_markdown", "No cheatsheet available."))
        st.divider()
        st.markdown("#### Drills")
        for d_idx, drill in enumerate(topic_data.get("drills", []), 1):
            st.markdown(f"**{d_idx:02d}.** {drill.get('prompt')}")
            c_h, c_s = st.columns(2)
            with c_h.expander("Hint"):
                st.write(drill.get("hint", ""))
            with c_s.expander("Solution"):
                st.code(drill.get("solution_code", ""), language="sql")

    with sub_ai:
        st.markdown("#### Technical Coach Console")
        mode = st.radio(
            "Mode",
            ["Generate Study Guide", "Explain Concept", "Mock Interview Question"],
            horizontal=True,
            key="ai_mode",
        )
        default_topic = f"{next_mod['track']} — {next_mod['title']}" if next_mod else ""
        topic_input = st.text_input(
            "Topic or Question",
            value=default_topic,
            placeholder="e.g., Window functions vs GROUP BY, or p-value in A/B testing",
            key="ai_topic_input",
        )
        if st.button("Run Prompt", type="primary", key="btn_ask_coach") and topic_input.strip():
            weak_skills = [k for k, v in skills.items() if v == 0]
            full_prompt = f"Mode: {mode} | Unstarted tracks: {weak_skills} | Request: {topic_input.strip()}"
            st.write_stream(stream_ai_tutor(full_prompt, gemini_key))

# 4. ROUTINE & SKILL CHECK
with tab_routine:
    sub_log, sub_diag = st.tabs(["SESSION LOG", "SKILL VERIFICATION GATE"])

    with sub_log:
        col_form, col_hist = st.columns([1.2, 1])
        with col_form:
            st.markdown("#### Log Work Block")
            with st.form("daily_log_form"):
                c_d, c_h = st.columns(2)
                log_day = c_d.date_input("Date", value=date.today())
                hrs = c_h.number_input("Hours", min_value=0.5, max_value=12.0, value=float(hours_per_day), step=0.5)
                notes = st.text_input("Deliverable / Notes", placeholder="e.g., Completed SQL Joins + 2 drills")
                saved = st.form_submit_button("Commit Session", type="primary", use_container_width=True)

            if saved:
                log_study_session(conn, log_day.isoformat(), hrs, notes)
                st.success("Session logged.")
                st.rerun()

        with col_hist:
            st.markdown("#### History")
            if history:
                for dt_str, h, n in history[:8]:
                    note_part = f" — {n}" if n else ""
                    st.markdown(f"- **`{dt_str}`** · {h}h{note_part}")
            else:
                st.caption("No sessions recorded.")

    with sub_diag:
        claimed_strong = [k for k, v in skills.items() if v >= 2]
        if not claimed_strong:
            st.info("Set any skill slider to Level 2 or 3 in the sidebar to verify your baseline before bypassing modules.")
        else:
            q_list = diagnostic_quiz if isinstance(diagnostic_quiz, list) else diagnostic_quiz.get("questions", [])
            relevant_qs = [q for q in q_list if q.get("track") in claimed_strong]
            st.markdown(f"#### Verification Gate: {', '.join(claimed_strong)}")

            if not relevant_qs:
                st.caption("No diagnostic questions found for the selected tracks.")
            else:
                with st.form("diag_form"):
                    answers = {}
                    for i, q in enumerate(relevant_qs):
                        st.markdown(f"**{i + 1:02d}. [{q.get('track')}] {q.get('question')}**")
                        answers[i] = st.radio(
                            f"q_{i}",
                            q.get("options", []),
                            key=f"diag_{i}",
                            label_visibility="collapsed",
                        )
                    submit_diag = st.form_submit_button("Evaluate Baseline", type="primary")

                if submit_diag:
                    score = sum(1 for i, q in enumerate(relevant_qs) if answers.get(i) == q.get("answer"))
                    for i, q in enumerate(relevant_qs):
                        if answers.get(i) != q.get("answer"):
                            st.warning(f"Q{i + 1:02d} [{q.get('track')}]: {q.get('explanation')}")
                    pct = round((score / len(relevant_qs)) * 100)
                    if pct >= 80:
                        st.success(f"VERIFIED ({pct}%) — Bypassed modules confirmed.")
                    else:
                        st.error(f"BELOW THRESHOLD ({pct}%) — Lower the slider by 1 level to include fundamentals.")

# 5. PORTFOLIO & ATS CAREER STUDIO
with tab_portfolio:
    sub_proj, sub_ats = st.tabs(["PORTFOLIO & README BUILDER", "ATS JD GAP ANALYZER"])

    with sub_proj:
        proj_titles = [f"{p['title']} ({p['est_days']})" for p in PORTFOLIO_PROJECTS]
        chosen_proj_label = st.selectbox("Select Project Blueprint", proj_titles, key="proj_sel")
        selected_proj = PORTFOLIO_PROJECTS[proj_titles.index(chosen_proj_label)]

        p_left, p_right = st.columns([1.1, 1])

        with p_left:
            st.markdown(f"#### {selected_proj['title']}")
            st.markdown(
                render_tags(selected_proj["stack"] + [selected_proj["difficulty"]]),
                unsafe_allow_html=True,
            )
            st.info(f"**Business Problem:** {selected_proj['business_problem']}")
            st.write("**Dataset:**", selected_proj["dataset_idea"])

            st.markdown("##### Execution Checklist")
            for s_idx, step_text in enumerate(selected_proj["steps"], 1):
                st.checkbox(f"{s_idx:02d}. {step_text}", key=f"pstep_{selected_proj['id']}_{s_idx}")

        with p_right:
            st.markdown("#### Resume & GitHub Spec")
            m1, m2 = st.columns(2)
            vol_val = m1.text_input("Rows / Records", value="25,000+", key=f"m_vol_{selected_proj['id']}")
            pct_val = m2.text_input("Key % / Metric", value="14%", key=f"m_pct_{selected_proj['id']}")
            seg_val = st.text_input(
                "Scope (Categories / Months / Tools)",
                value="6 categories & 12 months",
                key=f"m_seg_{selected_proj['id']}",
            )

            metric_map = {
                "X,000+": vol_val,
                "X%": pct_val,
                "X": seg_val,
                "one-time, repeat, and high-value": seg_val,
                "Power BI / Excel": "Power BI",
                "SQL / Python Pandas": "SQL and Python (Pandas)",
            }
            bullets = build_resume_bullets(selected_proj, metric_map)

            st.markdown("##### ATS Resume Bullets")
            st.code("\n".join(f"• {b}" for b in bullets), language="text")

            with st.expander("GitHub `README.md` Template"):
                readme_md = generate_project_readme(selected_proj, metric_map, bullets)
                st.code(readme_md, language="markdown")

            if st.button("Refine Bullets with AI", key=f"btn_polish_{selected_proj['id']}", use_container_width=True):
                polish_prompt = (
                    f"Rewrite these Data Analyst fresher resume bullets to be punchy, action-verb-led, and ATS-friendly "
                    f"for project '{selected_proj['title']}' ({', '.join(selected_proj['stack'])}):\n"
                    + "\n".join(f"- {b}" for b in bullets)
                    + "\nProvide 3 tightened bullets plus 1 quick interview talking point."
                )
                st.write_stream(stream_ai_tutor(polish_prompt, gemini_key))

    with sub_ats:
        st.markdown("#### Target Job Description Scanner")
        jd_input = st.text_area(
            "Job Description",
            height=190,
            placeholder="Paste requirements & responsibilities from a Data Analyst JD (SQL, Pandas, Power BI, cohort/funnel, A/B testing...)",
            key="jd_analyzer_text",
            label_visibility="collapsed",
        )

        a1, a2 = st.columns(2)
        run_jd = a1.button("Run ATS Keyword Scan", type="primary", use_container_width=True, key="btn_run_jd")
        ai_jd = a2.button("AI Deep JD Audit", use_container_width=True, key="btn_ai_jd")

        if run_jd and jd_input.strip():
            res = analyze_jd_match(jd_input, skills, completed_ids)
            st.metric("ATS KEYWORD COVERAGE", f"{res['match_pct']}%")

            c_ok, c_gap = st.columns(2)
            with c_ok:
                st.markdown("**Covered Keywords**")
                if res["matched"]:
                    st.markdown(render_tags(res["matched"], variant="ok"), unsafe_allow_html=True)
                else:
                    st.caption("No calibrated keywords matched yet.")

            with c_gap:
                st.markdown("**Missing ATS Keywords**")
                if res["missing"]:
                    st.markdown(render_tags(res["missing"], variant="gap"), unsafe_allow_html=True)
                else:
                    st.success("All detected JD keywords covered.")

            st.markdown("##### Gap-Closing Resume Bullets")
            st.code("\n".join(f"• {b}" for b in res["gap_bullets"]), language="text")

        if ai_jd and jd_input.strip():
            ai_jd_prompt = (
                f"Candidate calibrated skills (0-3 scale): {skills}.\n"
                f"Target Data Analyst JD:\n{jd_input.strip()}\n\n"
                "1. List top 6 ATS keywords from this JD.\n"
                "2. Identify the candidate's biggest 2 gaps.\n"
                "3. Write 3 tailored, honest resume bullets positioning the candidate's SQL/Pandas/BI prep studio and projects for this role."
            )
            st.write_stream(stream_ai_tutor(ai_jd_prompt, gemini_key))