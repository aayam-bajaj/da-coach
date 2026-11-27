"""ats_engine.py - ATS-style JD matching, skill-gap analysis and readiness scoring.

Pure Python (standard library only) and free of Streamlit imports, so every
function here is cheap to call on each rerun and easy to test in isolation.

Public API
----------
analyze_jd(...)                 -> keyword extraction + gap analysis for a pasted JD
suggest_gap_bullets(...)        -> 2 tailored resume bullets that close the gap
build_jd_audit_prompt(...)      -> prompt string for the optional AI Deep JD Audit
compute_readiness(...)          -> interview-readiness scorecard by track
restore/record/progress helpers -> keep portfolio checklist state alive across reruns
"""

from __future__ import annotations

import hashlib
import re

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
LEVEL_LABELS = {0: "Not started", 1: "Beginner", 2: "Intermediate", 3: "Advanced"}

TRACK_LABELS = {
    "SQL": "SQL",
    "Python": "Python (Pandas)",
    "Power BI": "Power BI / Tableau",
    "Excel": "Excel",
    "Stats": "Business Stats",
    "Portfolio": "Portfolio",
}

# curriculum.json module_id prefix -> sidebar skill key
_MODULE_PREFIX = {
    "EXCEL": "Excel",
    "PBI": "Power BI",
    "POWER BI": "Power BI",
    "SQL": "SQL",
    "PY": "Python",
    "PYTHON": "Python",
    "STATS": "Stats",
}
_TRACK_TO_PREFIX = {"Excel": "EXCEL", "Power BI": "PBI", "SQL": "SQL", "Python": "PY", "Stats": "STATS"}

PORTFOLIO_STATE_KEY = "ats_portfolio_progress"
PORTFOLIO_STEP_KEY = "pstep_{pid}_{idx}"  # same key format app.py already uses
JD_MAX_PROMPT_CHARS = 5000

SAMPLE_JD = """Data Analyst - E-commerce Analytics
About the role
You will turn raw order and customer data into insights that guide pricing, retention and marketing decisions.
Responsibilities:
- Write complex SQL queries (joins, CTEs, window functions) to analyze large datasets
- Build and maintain Power BI dashboards and KPI reports for stakeholders
- Clean and analyze data in Python (Pandas, NumPy) and Excel (pivot tables, XLOOKUP)
- Design and analyze A/B tests; communicate findings through data storytelling
Requirements:
- 0-2 years of experience in a data analyst role or internship
- Strong SQL and Excel skills; hands-on experience with Power BI or Tableau
- Working knowledge of statistics, hypothesis testing and regression
Nice to have:
- Experience with Snowflake or BigQuery, Git/GitHub, and ETL pipelines
- Familiarity with cohort analysis and retention metrics
"""


# --------------------------------------------------------------------------- #
# Keyword taxonomy
# reqs = alternatives (track, level) - the keyword is "covered" if ANY is met.
# An empty reqs tuple means the keyword sits outside the DA Coach roadmap.
# --------------------------------------------------------------------------- #
def _kw(name: str, category: str, reqs, *aliases: str) -> dict:
    return {
        "name": name,
        "category": category,
        "reqs": tuple(reqs),
        "aliases": tuple(dict.fromkeys([name.lower(), *aliases])),
    }


SKILL_TAXONOMY: list[dict] = [
    # --- SQL ---
    _kw("SQL", "SQL", [("SQL", 1)], "structured query language"),
    _kw("MySQL / PostgreSQL / SQL Server", "SQL", [("SQL", 1)],
        "mysql", "postgresql", "postgres", "sql server", "t-sql", "tsql", "sqlite", "oracle sql"),
    _kw("Joins", "SQL", [("SQL", 2)], "join", "inner join", "left join", "outer join", "table joins"),
    _kw("Aggregations / GROUP BY", "SQL", [("SQL", 1)],
        "group by", "aggregation", "aggregate functions", "aggregating data"),
    _kw("Subqueries", "SQL", [("SQL", 2)], "subquery", "sub-query", "nested queries"),
    _kw("CTEs", "SQL", [("SQL", 2)], "cte", "common table expression"),
    _kw("Window Functions", "SQL", [("SQL", 3)],
        "window function", "partition by", "row_number", "dense_rank", "running total"),
    _kw("Query Optimization", "SQL", [("SQL", 3)],
        "query optimization", "query optimisation", "query tuning", "execution plan", "performance tuning"),
    _kw("Cohort & Funnel Analysis", "SQL", [("SQL", 3)],
        "cohort analysis", "cohort", "funnel analysis", "funnel", "retention analysis"),
    _kw("Relational Databases", "SQL", [("SQL", 1)], "relational database", "rdbms"),
    # --- Python ---
    _kw("Python", "Python", [("Python", 1)]),
    _kw("Pandas", "Python", [("Python", 2)]),
    _kw("NumPy", "Python", [("Python", 2)]),
    _kw("Data Cleaning", "Python", [("Python", 2), ("Excel", 2)],
        "data cleansing", "data wrangling", "data preparation", "data preprocessing",
        "data munging", "data quality", "cleaning data"),
    _kw("Exploratory Data Analysis (EDA)", "Python", [("Python", 3)],
        "exploratory data analysis", "eda", "exploratory analysis"),
    _kw("Matplotlib / Seaborn", "Python", [("Python", 3)], "matplotlib", "seaborn", "plotly"),
    _kw("Jupyter Notebooks", "Python", [("Python", 1)], "jupyter", "jupyter notebook"),
    _kw("Automation / Scripting", "Python", [("Python", 3)],
        "automation", "automated reporting", "scripting", "automate reports"),
    _kw("APIs", "Python", [("Python", 3)], "api", "rest api", "web scraping"),
    _kw("ETL / Data Pipelines", "Workflow", [("Excel", 3), ("Python", 3)],
        "etl", "data pipeline", "data integration", "elt"),
    # --- BI ---
    _kw("Power BI", "BI", [("Power BI", 1)], "powerbi"),
    _kw("Tableau", "BI", [("Power BI", 1)]),
    _kw("DAX", "BI", [("Power BI", 2)]),
    _kw("Data Modeling", "BI", [("Power BI", 2)],
        "data modelling", "star schema", "dimensional modeling", "dimensional modelling"),
    _kw("Dashboards", "BI", [("Power BI", 1), ("Excel", 3)], "dashboard", "dashboarding"),
    _kw("Data Visualization", "BI", [("Power BI", 1), ("Python", 3)],
        "data visualisation", "visualization", "visualisation", "data viz"),
    _kw("KPIs & Metrics", "BI", [("Power BI", 1)],
        "kpi", "key performance indicator", "performance metrics", "business metrics"),
    _kw("Reporting", "BI", [("Power BI", 1), ("Excel", 2)],
        "ad hoc reporting", "ad-hoc reporting", "bi reporting", "business reporting", "report building"),
    _kw("Business Intelligence", "BI", [("Power BI", 1)], "bi tools", "bi developer"),
    _kw("Power Query", "BI", [("Power BI", 1), ("Excel", 3)], "m language"),
    _kw("Row-Level Security", "BI", [("Power BI", 3)], "row level security", "rls"),
    # --- Excel ---
    _kw("Excel", "Excel", [("Excel", 1)], "ms excel", "microsoft excel", "google sheets", "spreadsheet"),
    _kw("Excel Formulas", "Excel", [("Excel", 1)], "formulas", "excel functions"),
    _kw("Pivot Tables", "Excel", [("Excel", 2)], "pivot table", "pivottable", "pivot charts"),
    _kw("Lookups (XLOOKUP / VLOOKUP)", "Excel", [("Excel", 2)],
        "xlookup", "vlookup", "hlookup", "index match", "index-match", "lookup functions"),
    _kw("Advanced Excel", "Excel", [("Excel", 3)], "power pivot", "advanced excel"),
    # --- Stats ---
    _kw("Statistics", "Stats", [("Stats", 1)],
        "statistical analysis", "descriptive statistics", "statistical", "statistical methods"),
    _kw("Probability", "Stats", [("Stats", 1)], "distributions", "probability distributions"),
    _kw("Confidence Intervals", "Stats", [("Stats", 2)], "confidence interval"),
    _kw("Hypothesis Testing", "Stats", [("Stats", 2)],
        "hypothesis test", "t-test", "chi-square", "anova", "significance testing",
        "p-value", "statistical significance"),
    _kw("Regression", "Stats", [("Stats", 2)], "linear regression", "regression analysis", "correlation"),
    _kw("Logistic Regression", "Stats", [("Stats", 3)]),
    _kw("A/B Testing", "Stats", [("Stats", 3)],
        "a/b test", "ab testing", "split testing", "experimentation", "experiment design"),
    # --- Business / portfolio-evidenced ---
    _kw("Stakeholder Communication", "Business", [("Portfolio", 1)],
        "stakeholder", "stakeholder management", "cross-functional", "cross functional"),
    _kw("Data Storytelling", "Business", [("Portfolio", 1)],
        "storytelling", "data story", "present findings", "communicate insights",
        "communicating insights", "presentation skills"),
    _kw("Business Insights", "Business", [("Portfolio", 1)],
        "actionable insights", "business insights", "data-driven", "data driven"),
    _kw("Ad-Hoc Analysis", "Business", [("Portfolio", 1)], "ad hoc analysis", "ad-hoc analysis", "ad hoc"),
    _kw("Requirements Gathering", "Business", [("Portfolio", 1)],
        "business requirements", "business analysis", "requirement gathering"),
    _kw("Data Validation", "Business", [("Portfolio", 1)], "data integrity", "data accuracy", "reconciliation"),
    _kw("Git / GitHub", "Business", [("Portfolio", 2)], "git", "github", "version control"),
    # --- Outside the DA Coach roadmap (honest gaps) ---
    _kw("Snowflake", "Tools", [], ),
    _kw("BigQuery", "Tools", [], "google bigquery"),
    _kw("Redshift", "Tools", [], "amazon redshift"),
    _kw("Cloud (AWS / Azure / GCP)", "Tools", [], "aws", "azure", "gcp", "google cloud"),
    _kw("Spark / Databricks", "Tools", [], "pyspark", "spark", "databricks", "hadoop", "big data"),
    _kw("dbt / Airflow", "Tools", [], "dbt", "airflow"),
    _kw("Looker / Qlik / QuickSight", "Tools", [],
        "looker", "looker studio", "qlik", "qlikview", "quicksight", "data studio"),
    _kw("R / SAS", "Tools", [], "rstudio", "r programming", "sas"),
    _kw("Machine Learning", "Tools", [], "scikit-learn", "sklearn", "predictive modeling", "predictive analytics"),
    _kw("Forecasting / Time Series", "Tools", [], "forecasting", "time series"),
    _kw("VBA / Macros", "Tools", [], "vba", "macros", "macro"),
    _kw("Google Analytics", "Tools", [], "ga4", "web analytics"),
    _kw("CRM / ERP (Salesforce, SAP)", "Tools", [], "salesforce", "crm", "sap", "erp"),
    _kw("Agile / Jira", "Tools", [], "agile", "scrum", "jira"),
    _kw("Data Warehousing", "Tools", [], "data warehouse", "data warehouses", "dwh"),
]

_SKILL_BY_NAME = {s["name"]: s for s in SKILL_TAXONOMY}


def _build_alias_index() -> tuple[dict[str, str], re.Pattern]:
    alias_to_name: dict[str, str] = {}
    for skill in SKILL_TAXONOMY:
        for alias in skill["aliases"]:
            variants = {alias} if alias.endswith("s") else {alias, alias + "s"}
            for v in variants:
                alias_to_name.setdefault(v, skill["name"])
    ordered = sorted(alias_to_name, key=len, reverse=True)
    pattern = re.compile(r"(?<![a-z0-9+#])(" + "|".join(re.escape(a) for a in ordered) + r")(?![a-z0-9+#])")
    return alias_to_name, pattern


_ALIAS_TO_NAME, _ALIAS_PATTERN = _build_alias_index()

# --------------------------------------------------------------------------- #
# Section / emphasis heuristics (deterministic)
# --------------------------------------------------------------------------- #
_REQ_HDR = re.compile(
    r"^(?:required|requirements?|must[- ]have|minimum qualifications?|basic qualifications?|"
    r"what you(?:'|’)?ll need|what we(?:'|’)?re looking for|qualifications?|essential|you have)\b"
)
_PREF_HDR = re.compile(
    r"^(?:preferred|nice[- ]to[- ]have|bonus|good to have|desired|a plus|plus points?)\b"
)
_RESET_HDR = re.compile(
    r"^(?:responsibilit|what you(?:'|’)?ll do|about |who we are|benefits|perks|why join|"
    r"company overview|job (?:summary|description|overview))"
)
_REQ_INLINE = re.compile(r"\b(?:must|required|requires?|essential|mandatory|minimum|proficien(?:t|cy)|strong)\b")
_PREF_INLINE = re.compile(
    r"\b(?:preferred|nice to have|nice-to-have|bonus|a plus|is a plus|desirable|good to have|ideally)\b"
)
_BULLET_STRIP = re.compile(r"^[\s\-\*•●▪>#]+")
_SPLIT = re.compile(r"[\r\n]+|(?<=[.;!?])\s+")


def jd_fingerprint(text: str) -> str:
    return hashlib.sha1((text or "").strip().encode("utf-8")).hexdigest()[:12]


def score_tone(pct: int) -> str:
    """Map a 0-100 score to a colour tone used by the UI pills / bars."""
    return "high" if pct >= 70 else "mid" if pct >= 40 else "low"


# --------------------------------------------------------------------------- #
# Skill levels (calibration + completed modules + portfolio evidence)
# --------------------------------------------------------------------------- #
def parse_module_id(module_id: str) -> tuple[str | None, int]:
    m = re.match(r"^\s*(.+?)[-_ ]L(\d+)\s*$", str(module_id), flags=re.I)
    if not m:
        return None, 0
    track = _MODULE_PREFIX.get(m.group(1).strip().upper())
    return track, int(m.group(2))


def portfolio_level(steps_done: int) -> int:
    return 2 if steps_done >= 4 else 1 if steps_done >= 1 else 0


def effective_levels(skills: dict, completed_ids, portfolio_steps_done: int = 0) -> dict[str, int]:
    eff = {k: int(v) for k, v in skills.items()}
    for module_id in completed_ids:
        track, lvl = parse_module_id(module_id)
        if track:
            eff[track] = max(eff.get(track, 0), lvl)
    eff["Portfolio"] = portfolio_level(portfolio_steps_done)
    return eff


# --------------------------------------------------------------------------- #
# JD keyword extraction + gap analysis
# --------------------------------------------------------------------------- #
def extract_jd_keywords(jd_text: str, top_n: int = 30) -> list[dict]:
    """Deterministic taxonomy match with light section/emphasis weighting."""
    hits: dict[str, dict] = {}
    mode = "default"
    for raw in _SPLIT.split(jd_text or ""):
        line = _BULLET_STRIP.sub("", raw).replace("**", "").strip()
        if not line:
            continue
        low = line.lower()
        if len(low) <= 80 and not low.endswith("."):
            if _PREF_HDR.match(low):
                mode = "preferred"
            elif _REQ_HDR.match(low):
                mode = "required"
            elif _RESET_HDR.match(low):
                mode = "default"

        if _PREF_INLINE.search(low) or mode == "preferred":
            tag, mult = "preferred", 0.6
        elif _REQ_INLINE.search(low) or mode == "required":
            tag, mult = "required", 1.5
        else:
            tag, mult = "default", 1.0

        for match in _ALIAS_PATTERN.finditer(low):
            name = _ALIAS_TO_NAME[match.group(1)]
            rec = hits.setdefault(name, {"count": 0, "weight": 0.0, "required": 0, "preferred": 0})
            rec["count"] += 1
            rec["weight"] += mult
            if tag == "required":
                rec["required"] += 1
            elif tag == "preferred":
                rec["preferred"] += 1

    results = []
    for name, rec in hits.items():
        if rec["required"]:
            priority = "Must-have"
        elif rec["preferred"] == rec["count"]:
            priority = "Nice-to-have"
        else:
            priority = "Core"
        skill = _SKILL_BY_NAME[name]
        results.append(
            {
                "name": name,
                "category": skill["category"],
                "count": rec["count"],
                "importance": round(min(rec["weight"], 4.0), 2),
                "priority": priority,
            }
        )
    results.sort(key=lambda r: (-r["importance"], -r["count"], r["name"]))
    return results[:top_n]


def _evaluate_reqs(reqs, eff: dict[str, int]):
    """Return (covered, track, level) - the met alternative, or the closest unmet one."""
    best = None
    for track, level in reqs:
        gap = level - eff.get(track, 0)
        if gap <= 0:
            return True, track, level
        if best is None or gap < best[0]:
            best = (gap, track, level)
    return False, best[1], best[2]


def _need_text(track: str, level: int) -> str:
    if track == "Portfolio":
        return "Portfolio - ship one project" if level >= 2 else "Portfolio - start a project"
    return f"{TRACK_LABELS.get(track, track)} - Level {level} ({LEVEL_LABELS[level]})"


def analyze_jd(
    jd_text: str,
    skills: dict,
    completed_ids,
    portfolio_steps_done: int = 0,
    module_titles: dict | None = None,
    top_n: int = 30,
) -> dict:
    """Extract top keywords from a JD and compare them with what the user can show."""
    module_titles = module_titles or {}
    eff = effective_levels(skills, completed_ids, portfolio_steps_done)
    keywords = extract_jd_keywords(jd_text, top_n=top_n)

    matched, gaps, outside = [], [], []
    total_weight = covered_weight = 0.0
    for kw in keywords:
        skill = _SKILL_BY_NAME[kw["name"]]
        item = dict(kw)
        total_weight += kw["importance"]
        if not skill["reqs"]:
            item.update(status="outside", need="Outside DA Coach roadmap", module_id="", module_title="")
            outside.append(item)
            continue
        covered, track, level = _evaluate_reqs(skill["reqs"], eff)
        module_id = f"{_TRACK_TO_PREFIX[track]}-L{level}" if track in _TRACK_TO_PREFIX else ""
        item.update(
            need=_need_text(track, level),
            module_id=module_id,
            module_title=module_titles.get(module_id, ""),
            you_have=LEVEL_LABELS[eff.get(track, 0)],
        )
        if covered:
            item["status"] = "covered"
            covered_weight += kw["importance"]
            matched.append(item)
        else:
            item["status"] = "gap"
            gaps.append(item)

    score = int(round(100 * covered_weight / total_weight)) if total_weight else 0
    return {
        "keywords": keywords,
        "matched": matched,
        "gaps": gaps,
        "outside": outside,
        "ats_score": score,
        "word_count": len((jd_text or "").split()),
    }


# --------------------------------------------------------------------------- #
# Tailored bullets that close the gap
# --------------------------------------------------------------------------- #
_PROJECT_CONTEXT = {
    "proj_retail_sql_bi": ("e-commerce orders and returns", "net-revenue leakage"),
    "proj_churn_retention": ("customer order history", "early repeat-purchase drop-off"),
    "proj_messy_pipeline_eda": ("messy operational exports", "data-quality errors"),
}

_BULLET_TEMPLATES = {
    "SQL": "Applied {kw} in SQL across [X,000+] rows of {ctx} to isolate [X%] of {outcome}, turning the findings into [N] stakeholder-ready recommendations.",
    "Python": "Built a reproducible Python (Pandas) workflow using {kw} on [X,000+] rows of {ctx}, cutting manual prep time by [X%] and surfacing {outcome}.",
    "BI": "Designed a [Power BI / Tableau] solution featuring {kw} over {ctx}, giving stakeholders self-serve visibility into [X] KPIs and reducing reporting turnaround by [X%].",
    "Excel": "Streamlined {ctx} reporting in Excel using {kw}, replacing [X] manual steps and cutting weekly turnaround from [X] hours to [X].",
    "Stats": "Applied {kw} to {ctx} to validate segment differences at [95%] confidence, informing a decision projected to reduce {outcome} by [X%].",
    "Business": "Used {kw} to translate {ctx} analysis into [N] actionable recommendations on {outcome}, presented to [audience] and adopted in [decision / process].",
    "Workflow": "Automated {kw} for {ctx}, standardizing [X] recurring data-prep steps and reducing refresh time by [X%].",
}


def _join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def suggest_gap_bullets(analysis: dict, project_id: str = "", n: int = 2) -> list[dict]:
    """Return up to n resume bullets. Gap keywords first; matched ones only to reinforce."""
    ctx, outcome = _PROJECT_CONTEXT.get(project_id, ("[dataset]", "[business outcome]"))

    def group(items):
        grouped: dict[str, list[dict]] = {}
        for it in items:
            if it["category"] in _BULLET_TEMPLATES:
                grouped.setdefault(it["category"], []).append(it)
        order = sorted(grouped, key=lambda c: -sum(i["importance"] for i in grouped[c]))
        return grouped, order

    chosen: list[tuple[str, list[dict], str]] = []
    grouped, order = group(analysis.get("gaps", []))
    for cat in order:
        chosen.append((cat, grouped[cat][:3], "gap"))
        if len(chosen) == n:
            break
    if len(chosen) < n and order and len(grouped[order[0]]) > 3:
        chosen.append((order[0], grouped[order[0]][3:6], "gap"))

    if len(chosen) < n:
        used = {c for c, _, _ in chosen}
        m_grouped, m_order = group(analysis.get("matched", []))
        for cat in m_order:
            if cat in used:
                continue
            chosen.append((cat, m_grouped[cat][:3], "reinforce"))
            if len(chosen) == n:
                break

    bullets = []
    for cat, items, mode in chosen[:n]:
        names = [i["name"] for i in items]
        bullets.append(
            {
                "text": _BULLET_TEMPLATES[cat].format(kw=_join_names(names), ctx=ctx, outcome=outcome),
                "keywords": names,
                "mode": mode,
            }
        )
    return bullets


# --------------------------------------------------------------------------- #
# Optional AI Deep JD Audit prompt (streamed by the caller via stream_ai_tutor)
# --------------------------------------------------------------------------- #
def build_jd_audit_prompt(jd_text: str, analysis: dict, skills: dict, project_title: str = "") -> str:
    def names(items):
        return ", ".join(i["name"] for i in items) or "none"

    calibration = ", ".join(f"{k}={LEVEL_LABELS[int(v)]}" for k, v in skills.items())
    jd = (jd_text or "").strip()[:JD_MAX_PROMPT_CHARS]
    focus = f"Portfolio project in focus: {project_title}.\n" if project_title else ""
    return (
        "Audit a fresher's resume fit against this Data Analyst job description for ATS screening.\n\n"
        f"JD (may be truncated):\n<<<\n{jd}\n>>>\n\n"
        f"Deterministic scan - ATS keyword match: {analysis['ats_score']}%.\n"
        f"Covered: {names(analysis['matched'])}.\n"
        f"Gaps the candidate can still learn: {names(analysis['gaps'])}.\n"
        f"Tools outside the candidate's roadmap: {names(analysis['outside'])}.\n"
        f"Self-calibrated skills: {calibration}.\n{focus}\n"
        "Reply in under 250 words using exactly this structure:\n"
        "1. **Phrases to mirror** - 5 exact phrases from the JD worth echoing on the resume.\n"
        "2. **Risk flags** - 2 claims this candidate should not make without proof.\n"
        "3. **Two resume bullets** - close the biggest gap (action verb + tool + metric placeholders).\n"
        "4. **Likely interview question** - with a one-line answer outline."
    )


# --------------------------------------------------------------------------- #
# Portfolio checklist persistence (widget keys are cleaned up by Streamlit when
# a project is not on screen, so the per-step booleans are mirrored to a plain
# session key). `state` is st.session_state or any dict-like object.
# --------------------------------------------------------------------------- #
def restore_portfolio_steps(state, project: dict) -> None:
    saved = (state.get(PORTFOLIO_STATE_KEY) or {}).get(project["id"])
    if not saved:
        return
    for idx, flag in enumerate(saved, 1):
        key = PORTFOLIO_STEP_KEY.format(pid=project["id"], idx=idx)
        if key not in state:
            state[key] = bool(flag)


def record_portfolio_progress(state, project: dict) -> None:
    if PORTFOLIO_STATE_KEY not in state:
        state[PORTFOLIO_STATE_KEY] = {}
    flags = [
        bool(state.get(PORTFOLIO_STEP_KEY.format(pid=project["id"], idx=i)))
        for i in range(1, len(project["steps"]) + 1)
    ]
    state[PORTFOLIO_STATE_KEY][project["id"]] = flags


def sync_portfolio_state(state, projects: list[dict]) -> None:
    """Call once near the top of the script: refill checklist widget keys that Streamlit
    cleaned up, then mirror every project's current flags into the plain session key."""
    for project in projects:
        restore_portfolio_steps(state, project)
        record_portfolio_progress(state, project)


def portfolio_progress(state, projects: list[dict]) -> tuple[int, int]:
    """(steps done across all projects, target = steps in the two biggest projects)."""
    store = state.get(PORTFOLIO_STATE_KEY) or {}
    done = sum(sum(1 for f in flags if f) for flags in store.values())
    target = sum(sorted((len(p["steps"]) for p in projects), reverse=True)[:2]) or 1
    return done, target


# --------------------------------------------------------------------------- #
# Interview readiness scorecard
# --------------------------------------------------------------------------- #
_CARD_DEFS = [
    ("SQL", ["SQL"], "Joins, CTEs and window functions written cleanly under time pressure."),
    ("Python / Pandas", ["Python"], "Pandas cleaning, groupby/merge and an EDA workflow with clear visuals."),
    ("BI / Excel", ["Power BI", "Excel"], "KPI dashboards, sound data modeling, pivot tables and DAX basics."),
    ("Business Stats", ["Stats"], "A/B tests, hypothesis testing and explaining uncertainty to non-analysts."),
]
_PORTFOLIO_FOCUS = "2-3 end-to-end projects: business question, metrics, clean README and a dashboard."


def _stage(pct: int) -> str:
    return "Interview ready" if pct >= 80 else "Almost there" if pct >= 55 else "Building" if pct >= 25 else "Getting started"


def compute_readiness(
    skills: dict,
    queue: list[dict],
    skipped: list[str],
    completed_ids,
    portfolio_done: int,
    portfolio_target: int,
) -> list[dict]:
    """Readiness per track. Mirrors app.py: skipped modules count as done."""
    eff = effective_levels(skills, completed_ids, portfolio_done)
    cards = []
    for label, tracks, focus in _CARD_DEFS:
        total = done = 0
        for track in tracks:
            in_queue = [m for m in queue if m["track"] == track]
            skipped_n = sum(1 for s in skipped if s.startswith(f"{track} — "))
            total += skipped_n + len(in_queue)
            done += skipped_n + sum(1 for m in in_queue if m["module_id"] in completed_ids)
        pct = int(round(100 * done / total)) if total else 0
        nxt = next((m for m in queue if m["track"] in tracks and m["module_id"] not in completed_ids), None)
        level = int(round(sum(eff.get(t, 0) for t in tracks) / len(tracks)))
        cards.append(
            {
                "label": label,
                "pct": pct,
                "done": done,
                "total": total,
                "unit": "modules",
                "level": level,
                "stage": _stage(pct),
                "tone": score_tone(pct),
                "focus": focus,
                "next": f"{nxt['title']} ({nxt['estimated_hours']}h)" if nxt else "",
            }
        )

    pf_pct = min(100, int(round(100 * portfolio_done / portfolio_target))) if portfolio_target else 0
    cards.append(
        {
            "label": "Portfolio",
            "pct": pf_pct,
            "done": min(portfolio_done, portfolio_target),
            "total": portfolio_target,
            "unit": "project steps",
            "level": 3 if pf_pct >= 100 else 2 if pf_pct >= 50 else 1 if pf_pct > 0 else 0,
            "stage": _stage(pf_pct),
            "tone": score_tone(pf_pct),
            "focus": _PORTFOLIO_FOCUS,
            "next": "Tick the next checklist step in your selected project" if pf_pct < 100 else "",
        }
    )
    return cards