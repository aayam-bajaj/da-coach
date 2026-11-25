import json
import sqlite3
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus
import streamlit as st

from youtube_curator import fetch_top_youtube_resources
from sql_sandbox import SQL_CHALLENGES, execute_and_grade
from ai_tutor import stream_ai_tutor

st.set_page_config(
    page_title="DA Coach — Data Analyst Prep",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Deep Obsidian Canvas with Subtle Radial Chrome Glow */
    .stApp {
        background: radial-gradient(circle at 15% 10%, #1E222D 0%, #090A0F 55%, #050608 100%);
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    /* Liquid Chrome Metallic Title */
    h1 {
        background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 35%, #64748B 50%, #F8FAFC 75%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.03em;
    }

    /* Frosted Glass + Chrome Edge Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 34, 45, 0.7), rgba(13, 15, 22, 0.85));
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 0.18);
        border-top: 1px solid rgba(255, 255, 255, 0.35);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        padding: 14px 18px;
        border-radius: 14px;
    }

    /* Chrome Expanders & Containers */
    div[data-testid="stExpander"] {
        background: rgba(18, 20, 29, 0.65);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(203, 213, 225, 0.15);
        border-radius: 12px;
    }

    /* Liquid Silver Primary Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #F8FAFC 0%, #CBD5E1 50%, #94A3B8 100%) !important;
        color: #090A0F !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(226, 232, 240, 0.2);
        transition: all 0.2s ease;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.35);
    }

    /* Glass Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D0F16 0%, #07080C 100%);
        border-right: 1px solid rgba(226, 232, 240, 0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Persistent SQLite Storage (progress.db) ---
@st.cache_resource
def get_conn():
    conn = sqlite3.connect("progress.db", check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS completed_modules (
            module_id TEXT PRIMARY KEY,
            completed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_logs (
            log_date TEXT PRIMARY KEY,
            hours_logged REAL,
            notes TEXT
        )
    """)
    conn.commit()
    return conn


conn = get_conn()


def get_completed_set():
    return {r[0] for r in conn.execute("SELECT module_id FROM completed_modules").fetchall()}


def toggle_module_status(module_id: str, is_done: bool):
    if is_done:
        conn.execute(
            "INSERT OR REPLACE INTO completed_modules (module_id, completed_at) VALUES (?, ?)",
            (module_id, datetime.now().isoformat()),
        )
    else:
        conn.execute("DELETE FROM completed_modules WHERE module_id = ?", (module_id,))
    conn.commit()


def log_study_session(log_dt: str, hours: float, notes: str):
    conn.execute(
        "INSERT OR REPLACE INTO study_logs (log_date, hours_logged, notes) VALUES (?, ?, ?)",
        (log_dt, hours, notes),
    )
    conn.commit()


def export_progress_json() -> str:
    comp = [
        {"module_id": r[0], "completed_at": r[1]}
        for r in conn.execute("SELECT module_id, completed_at FROM completed_modules").fetchall()
    ]
    logs = [
        {"log_date": r[0], "hours_logged": r[1], "notes": r[2]}
        for r in conn.execute("SELECT log_date, hours_logged, notes FROM study_logs").fetchall()
    ]
    return json.dumps({"completed_modules": comp, "study_logs": logs}, indent=2)


def import_progress_json(raw_text: str):
    payload = json.loads(raw_text)
    for item in payload.get("completed_modules", []):
        conn.execute(
            "INSERT OR REPLACE INTO completed_modules (module_id, completed_at) VALUES (?, ?)",
            (item["module_id"], item.get("completed_at") or datetime.now().isoformat()),
        )
    for item in payload.get("study_logs", []):
        conn.execute(
            "INSERT OR REPLACE INTO study_logs (log_date, hours_logged, notes) VALUES (?, ?, ?)",
            (item["log_date"], float(item["hours_logged"]), item.get("notes") or ""),
        )
    conn.commit()


def get_streak_and_hours():
    rows = conn.execute(
        "SELECT log_date, hours_logged, notes FROM study_logs WHERE hours_logged > 0 ORDER BY log_date DESC"
    ).fetchall()
    total_hours = sum(r[1] for r in rows)
    logged_dates = {date.fromisoformat(r[0]) for r in rows}

    streak = 0
    cursor = date.today()
    if cursor not in logged_dates:
        cursor = cursor - timedelta(days=1)
    while cursor in logged_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak, round(total_hours, 1), rows


# --- Load Curriculum & Study Data ---
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


def build_training_queue(raw_curriculum, skills):
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


# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🎯 Skill Calibration")
    skills = {
        "Excel": st.slider("Excel", 0, 3, 3),
        "Power BI": st.slider("Power BI / Tableau", 0, 3, 3),
        "SQL": st.slider("SQL", 0, 3, 0),
        "Python": st.slider("Python (Pandas)", 0, 3, 0),
        "Stats": st.slider("Business Stats", 0, 3, 0),
    }

    st.markdown("### ⏱️ Weekly Schedule")
    hours_per_day = st.selectbox("Hours / day", [1, 2, 3, 4], index=1)
    days_per_week = st.slider("Study days / week", 3, 7, 5)
    weekly_budget = hours_per_day * days_per_week

    st.markdown("### 🤖 AI Tutor Key")
    gemini_key = st.text_input(
        "Gemini API Key (optional if set in Secrets)",
        type="password",
        placeholder="AIza...",
        key="gemini_api_key",
    )

    st.divider()
    streak, total_logged_hrs, _ = get_streak_and_hours()
    c1, c2 = st.columns(2)
    c1.metric("Streak", f"{streak}d")
    c2.metric("Logged", f"{total_logged_hrs}h")

    st.divider()
    st.markdown("### 💾 Backup Progress")
    st.download_button(
        "Export Progress JSON",
        data=export_progress_json(),
        file_name="da_coach_progress.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded_backup = st.file_uploader("Restore JSON", type=["json"], label_visibility="collapsed")
    if uploaded_backup is not None and st.button("Import Backup", use_container_width=True):
        try:
            import_progress_json(uploaded_backup.getvalue().decode("utf-8"))
            st.success("Progress restored!")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid backup file: {e}")


# --- Main Header & KPIs ---
skipped, queue = build_training_queue(curriculum, skills)
completed_ids = get_completed_set()

total_required = len(skipped) + len(queue)
done_count = len(skipped) + sum(1 for m in queue if m["module_id"] in completed_ids)
readiness_pct = int((done_count / total_required) * 100) if total_required else 0
remaining_hrs = sum(m["estimated_hours"] for m in queue if m["module_id"] not in completed_ids)

st.title("Data Analyst Prep Coach")
st.caption("Strength-calibrated roadmaps • Curated YouTube playlists • Cheatsheets & drills • SQL Sandbox • AI Tutor")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Job Readiness", f"{readiness_pct}%")
k2.metric("Modules Done", f"{done_count}/{total_required}")
k3.metric("Weekly Target", f"{weekly_budget} hrs")
k4.metric("Est. Weeks Left", f"{round(remaining_hrs / weekly_budget, 1) if weekly_budget else 0}")

st.progress(readiness_pct / 100)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏋️ Training Queue",
    "🧪 Skill Check",
    "📘 Cheatsheets & Drills",
    "📅 Daily Log",
    "💻 SQL Sandbox",
    "🤖 AI Tutor",
])

# TAB 1: Dynamic Roadmap + Curated Videos
with tab1:
    left, right = st.columns([1, 2.2])
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
            st.success("All modules complete for your current skill settings!")
        for idx, mod in enumerate(queue, 1):
            is_done = mod["module_id"] in completed_ids
            icon = "✅" if is_done else "⬜"
            header = f"{icon} {idx}. [{mod['track']}] {mod['title']} — {mod['estimated_hours']}h"
            with st.expander(header, expanded=(idx == 1 and not is_done)):
                checked = st.checkbox("Mark Module Complete", value=is_done, key=f"chk_{mod['module_id']}")
                if checked != is_done:
                    toggle_module_status(mod["module_id"], checked)
                    st.rerun()

                if mod["key_topics"]:
                    st.write("**Key Topics:**", " • ".join(str(t) for t in mod["key_topics"]))

                fallback_url = f"https://www.youtube.com/results?search_query={quote_plus(mod['youtube_search_query'] + ' playlist')}"
                b1, b2 = st.columns(2)
                fetch_clicked = b1.button("Fetch Top Playlists", key=f"yt_{idx}", use_container_width=True)
                b2.link_button("YouTube Search Results", fallback_url, use_container_width=True)

                if fetch_clicked:
                    with st.spinner("Searching YouTube..."):
                        videos = fetch_top_youtube_resources(mod["youtube_search_query"], max_results=3)
                        for v in videos:
                            views_str = f" • {v['views']:,} views" if v.get("views") else ""
                            st.markdown(f"- [{v['title']}]({v['url']}) — *{v['channel']}*{views_str}")

# TAB 2: Diagnostic Gate
with tab2:
    claimed_strong = [k for k, v in skills.items() if v >= 2]
    if not claimed_strong:
        st.info("Set any skill slider to 2 or 3 in the sidebar to run a verification check.")
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
                    st.markdown(f"**{i+1}. [{q.get('track')}] {q.get('question')}**")
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
                        st.warning(f"Q{i+1} [{q.get('track')}]: {q.get('explanation')}")
                pct = round((score / len(relevant_qs)) * 100)
                if pct >= 80:
                    st.success(f"Passed ({pct}%) — your skipped modules stay unlocked.")
                else:
                    st.error(f"Scored {pct}% — consider lowering that slider by 1 level.")

# TAB 3: Cheatsheets & Practice Drills
with tab3:
    vault_items = list(study_vault.items()) if isinstance(study_vault, dict) else [
        (item.get("topic", f"Topic {i+1}"), item) for i, item in enumerate(study_vault)
    ]
    topic_names = [name for name, _ in vault_items]
    selected_topic = st.selectbox("Select Topic", topic_names)
    topic_data = dict(vault_items).get(selected_topic, {})

    st.markdown(topic_data.get("cheatsheet_markdown", "No cheatsheet available."))
    st.divider()
    st.markdown("#### Hands-On Drills")
    for d_idx, drill in enumerate(topic_data.get("drills", []), 1):
        st.markdown(f"**Drill {d_idx}:** {drill.get('prompt')}")
        c_h, c_s = st.columns(2)
        with c_h.expander("Hint"):
            st.write(drill.get("hint", ""))
        with c_s.expander("Solution"):
            st.code(drill.get("solution_code", ""), language="sql")

# TAB 4: Daily Routine & Study Logger
with tab4:
    next_mod = next((m for m in queue if m["module_id"] not in completed_ids), None)
    if next_mod:
        st.info(
            f"**Today's Focus ({hours_per_day}h):** [{next_mod['track']}] {next_mod['title']} — "
            f"Watch 1 playlist video + complete 1 drill."
        )
    else:
        st.success("All queued modules completed!")

    with st.form("daily_log_form"):
        c_d, c_h = st.columns(2)
        log_day = c_d.date_input("Date", value=date.today())
        hrs = c_h.number_input("Hours studied", min_value=0.5, max_value=12.0, value=float(hours_per_day), step=0.5)
        notes = st.text_input("Session notes", placeholder="e.g., Finished SQL Joins + 2 drills")
        saved = st.form_submit_button("Log Session", type="primary")

    if saved:
        log_study_session(log_day.isoformat(), hrs, notes)
        st.success("Session logged!")
        st.rerun()

    _, _, history = get_streak_and_hours()
    if history:
        st.markdown("#### Recent Sessions")
        for dt_str, h, n in history[:7]:
            note_part = f" — {n}" if n else ""
            st.write(f"- **{dt_str}**: {h}h{note_part}")

# TAB 5: Interactive SQL Sandbox
with tab5:
    st.subheader("Interactive SQL Sandbox")
    with st.expander("Database Schema (`customers`, `products`, `orders`)", expanded=True):
        st.code(
            "customers(customer_id, name, city, segment, signup_date)\n"
            "products(product_id, product_name, category, unit_price)\n"
            "orders(order_id, customer_id, product_id, quantity, order_date, status)",
            language="sql",
        )

    challenge_titles = [c["title"] for c in SQL_CHALLENGES]
    chosen_title = st.selectbox("Select Challenge", challenge_titles)
    challenge = next(c for c in SQL_CHALLENGES if c["title"] == chosen_title)

    st.info(challenge["prompt"])
    user_sql = st.text_area("Write your SQL query:", height=150, placeholder="SELECT ...")

    c_run, c_help = st.columns(2)
    run_sql = c_run.button("Run & Grade SQL", type="primary", use_container_width=True)
    ai_hint = c_help.button("Ask AI Tutor to Review SQL", use_container_width=True)

    if run_sql and user_sql.strip():
        df_out, err, passed = execute_and_grade(user_sql, challenge["solution"])
        if err:
            st.error(err)
        else:
            st.dataframe(df_out, use_container_width=True)
            if passed:
                st.success("Exact match! Challenge solved.")
            else:
                st.warning("Query ran, but results don't match the expected output yet.")

    if ai_hint and user_sql.strip():
        review_prompt = (
            f"Problem: {challenge['prompt']}\n"
            f"User's SQL:\n{user_sql}\n"
            "Give a concise hint on any logic/syntax issue or optimization without giving the full answer."
        )
        st.write_stream(stream_ai_tutor(review_prompt, gemini_key))

# TAB 6: Streaming AI Tutor
with tab6:
    st.subheader("Live AI Data Analyst Tutor")
    mode = st.radio(
        "Mode",
        ["Generate Study Guide", "Explain Concept", "Mock Interview Question"],
        horizontal=True,
    )
    topic_input = st.text_input(
        "Topic or Question",
        placeholder="e.g., Window functions vs GROUP BY, or Explain p-value in A/B testing",
    )
    if st.button("Ask Coach", type="primary") and topic_input.strip():
        weak_skills = [k for k, v in skills.items() if v == 0]
        full_prompt = f"Mode: {mode} | Unstarted tracks: {weak_skills} | Request: {topic_input.strip()}"
        st.write_stream(stream_ai_tutor(full_prompt, gemini_key))