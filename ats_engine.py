import re

DA_KEYWORD_CATALOG = {
    "SQL": [
        "sql", "cte", "window function", "window functions", "joins", "left join",
        "group by", "having", "subquery", "subqueries", "postgresql", "mysql",
        "sqlite", "bigquery", "snowflake", "stored procedure", "query optimization",
    ],
    "Python (Pandas)": [
        "python", "pandas", "numpy", "data cleaning", "eda", "exploratory data analysis",
        "matplotlib", "seaborn", "jupyter", "etl", "scripting", "automation",
    ],
    "BI & Excel": [
        "excel", "vlookup", "xlookup", "pivot table", "pivot tables", "power query",
        "power bi", "dax", "tableau", "dashboard", "dashboards", "kpi", "kpis",
        "data visualization", "reporting",
    ],
    "Business & Stats": [
        "a/b testing", "ab testing", "hypothesis testing", "p-value", "regression",
        "cohort", "retention", "churn", "funnel", "forecasting", "segmentation",
        "stakeholder", "ad-hoc", "root cause", "business metrics",
    ],
}

TRACK_KEYWORDS = {
    "SQL": {
        "sql", "cte", "window function", "window functions", "joins", "left join",
        "group by", "having", "subquery", "subqueries", "postgresql", "mysql",
        "sqlite", "bigquery", "snowflake",
    },
    "Python": {
        "python", "pandas", "numpy", "data cleaning", "eda",
        "exploratory data analysis", "matplotlib", "seaborn", "etl",
    },
    "Excel": {"excel", "vlookup", "xlookup", "pivot table", "pivot tables", "power query"},
    "Power BI": {"power bi", "dax", "tableau", "dashboard", "dashboards", "data visualization"},
    "Stats": {
        "a/b testing", "ab testing", "hypothesis testing", "p-value",
        "regression", "cohort", "retention", "churn", "funnel", "forecasting",
    },
}


def analyze_jd_match(jd_text: str, skills: dict[str, int], completed_ids: set[str]) -> dict:
    cleaned = re.sub(r"[^a-z0-9/+\-\s]", " ", jd_text.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    found_by_cat: dict[str, list[str]] = {}
    all_found: list[str] = []

    for cat, keywords in DA_KEYWORD_CATALOG.items():
        hits = []
        for kw in keywords:
            pattern = r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"
            if re.search(pattern, cleaned):
                hits.append(kw)
                all_found.append(kw)
        if hits:
            found_by_cat[cat] = hits

    completed_blob = " ".join(completed_ids).lower()
    matched_skills: list[str] = []
    gap_skills: list[str] = []

    for kw in all_found:
        covered = False
        for track, t_kws in TRACK_KEYWORDS.items():
            if kw in t_kws:
                if skills.get(track, 0) >= 2 or track.lower() in completed_blob:
                    covered = True
                break
        if covered:
            matched_skills.append(kw)
        else:
            gap_skills.append(kw)

    total_hits = len(all_found)
    match_pct = int(round((len(matched_skills) / total_hits) * 100)) if total_hits else 0

    gap_bullets = []
    if any(k in gap_skills for k in ["sql", "cte", "window function", "window functions", "joins", "subquery", "subqueries"]):
        gap_bullets.append(
            "Wrote complex SQL queries using CTEs, multi-table JOINs, and window functions (RANK, LAG) to analyze retention, repeat purchase behavior, and monthly revenue trends."
        )
    if any(k in gap_skills for k in ["python", "pandas", "data cleaning", "eda", "exploratory data analysis"]):
        gap_bullets.append(
            "Automated end-to-end data cleaning and exploratory data analysis (EDA) in Python (Pandas, NumPy), resolving missing values, inconsistent formats, and outliers across raw operational datasets."
        )
    if any(k in gap_skills for k in ["power bi", "tableau", "dax", "dashboard", "dashboards", "excel", "pivot table", "pivot tables"]):
        gap_bullets.append(
            "Designed interactive KPI dashboards in Power BI / Excel with dynamic filters and DAX/calculated fields to surface margin leakage and regional performance drivers."
        )
    if any(k in gap_skills for k in ["a/b testing", "ab testing", "cohort", "funnel", "churn", "retention", "root cause"]):
        gap_bullets.append(
            "Conducted cohort retention and funnel conversion diagnostics to pinpoint customer drop-off stages and recommend data-backed optimization experiments."
        )
    if not gap_bullets:
        gap_bullets.append(
            "Translated raw multi-table business datasets into clean SQL/Pandas pipelines and executive-ready KPI summaries aligned with core stakeholder questions."
        )

    return {
        "match_pct": match_pct,
        "found_by_cat": found_by_cat,
        "matched": sorted(set(matched_skills)),
        "missing": sorted(set(gap_skills)),
        "gap_bullets": gap_bullets[:2],
    }


def compute_track_scorecard(
    skills: dict[str, int],
    queue: list[dict],
    skipped: list[str],
    completed_ids: set[str],
) -> list[dict]:
    tracks = ["SQL", "Python", "Power BI", "Excel", "Stats"]
    scorecard = []

    for tr in tracks:
        tr_mods = [m for m in queue if m["track"] == tr]
        tr_skipped = [s for s in skipped if s.startswith(f"{tr} —")]
        total = len(tr_mods) + len(tr_skipped)
        done = len(tr_skipped) + sum(1 for m in tr_mods if m["module_id"] in completed_ids)

        if total > 0:
            pct = int(round((done / total) * 100))
        else:
            pct = int(round((skills.get(tr, 0) / 3) * 100))

        status = "Interview Ready" if pct >= 80 else ("In Progress" if pct >= 35 else "Priority Gap")
        scorecard.append({
            "track": tr,
            "level": skills.get(tr, 0),
            "pct": pct,
            "done": done,
            "total": total,
            "status": status,
        })

    return scorecard


def generate_project_readme(project: dict, metrics: dict[str, str], bullets: list[str]) -> str:
    vol = metrics.get("X,000+", "25,000+").strip() or "25,000+"
    pct = metrics.get("X%", "14%").strip() or "14%"
    scope = metrics.get("X", "6 categories & 12 months").strip() or "6 categories & 12 months"
    stack_str = " | ".join(project.get("stack", []))
    steps_md = "\n".join(f"{i}. {s}" for i, s in enumerate(project.get("steps", []), 1))
    bullets_md = "\n".join(f"- {b}" for b in bullets)

    return f"""# {project['title']}

**Tech Stack:** {stack_str}  
**Dataset Scale:** {vol} records across {scope}

## 1. Business Problem
{project['business_problem']}

## 2. Dataset & Data Preparation
- **Source:** {project['dataset_idea']}
- **Cleaning & Validation:** Removed duplicate keys, standardized categorical casing/whitespace, parsed mixed date/currency strings, and audited null rates before and after transformation.

## 3. Analytical Workflow
{steps_md}

## 4. Key Findings & Resume Impact
{bullets_md}

## 5. Recommendations
- Prioritize high-impact segments identified in the diagnostic breakdown to capture an estimated **{pct}** improvement in core KPI efficiency.
- Automate recurring weekly metric tracking via parameterized SQL queries / Pandas scripts.

## 6. How to Reproduce
1. Clone this repository and place the raw CSV files inside `data/raw/`.
2. Run the cleaning & transformation scripts in `scripts/`.
3. Open the SQL queries in `sql/` or dashboard file in `dashboard/` to inspect metrics.
"""