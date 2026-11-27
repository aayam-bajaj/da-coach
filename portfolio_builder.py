PORTFOLIO_PROJECTS = [
    {
        "id": "proj_retail_sql_bi",
        "title": "E-Commerce Sales, Refund & Margin Diagnostic",
        "stack": ["SQL", "Excel / Power BI"],
        "difficulty": "Fresher — High Impact",
        "est_days": "4–6 days",
        "business_problem": (
            "An online retailer sees steady gross order volume but flat net profit. "
            "Identify which categories, cities, or discount tiers drive high return rates or margin leakage."
        ),
        "dataset_idea": "Public retail/e-commerce transaction CSV (orders, order_items, products, customers, returns).",
        "steps": [
            "Clean raw tables: remove duplicate order IDs, standardize dates/statuses, and separate cancelled/returned orders from completed revenue.",
            "Write SQL queries for gross revenue, net revenue, return rate %, top 5 SKUs/categories, and monthly revenue trend.",
            "Build a 1-page dashboard (Power BI / Tableau / Excel) with KPI cards, category margin comparison, and interactive filters.",
            "Extract 3 concrete recommendations (e.g., tightening free-return thresholds on low-margin items) and publish code + screenshots on GitHub.",
        ],
        "bullet_templates": [
            "Cleaned and modeled [X,000+] e-commerce transaction records using SQL, resolving duplicate orders and isolating cancelled/returned items to establish accurate net revenue.",
            "Built an interactive [Power BI / Excel] sales and return-rate dashboard tracking gross/net revenue, category margins, and monthly trends across [X] product categories.",
            "Identified [X%] revenue leakage from high-return SKUs and recommended targeted pricing/return policy adjustments projected to improve net margin by [X%].",
        ],
    },
    {
        "id": "proj_churn_retention",
        "title": "Customer Retention, Repeat Purchase & Cohort Analysis",
        "stack": ["SQL", "Python (Pandas)"],
        "difficulty": "Fresher — Interview Favorite",
        "est_days": "5–7 days",
        "business_problem": (
            "Acquisition costs are rising while repeat purchase rates lag. "
            "Measure customer retention across signup/first-order cohorts and pinpoint where buyers drop off."
        ),
        "dataset_idea": "Subscription or repeat-order transaction dataset with `customer_id`, `order_date`, and `order_value`.",
        "steps": [
            "Use SQL CTEs or Pandas to assign each customer's `first_order_month` and `order_month` to compute cohort retention rates.",
            "Segment customers by order frequency (one-time vs. repeat) and average order value (AOV) using `CASE WHEN` or Pandas `qcut`/bins.",
            "Plot a clean cohort retention heatmap and repeat-buyer revenue share chart in Python (`matplotlib`/`seaborn`) or BI.",
            "Summarize retention bottlenecks and propose an activation/re-engagement action tied to measurable KPIs.",
        ],
        "bullet_templates": [
            "Engineered customer cohort and repeat-purchase retention tables in [SQL / Python Pandas] across [X] months of order history to track early churn drop-offs.",
            "Segmented customers into [one-time, repeat, and high-value] tiers based on order frequency and spend, revealing that repeat buyers generated [X%] of total revenue.",
            "Visualized cohort retention trends and repeat-order intervals to highlight onboarding friction points and propose retention actions targeting a [X%] lift in 60-day repeat orders.",
        ],
    },
    {
        "id": "proj_messy_pipeline_eda",
        "title": "Automated Data Cleaning & Exploratory EDA Pipeline",
        "stack": ["Python (Pandas)", "Business Stats"],
        "difficulty": "Fresher — Technical Proof",
        "est_days": "4–5 days",
        "business_problem": (
            "Raw operational exports arrive with inconsistent date formats, currency strings, missing values, and extreme outliers. "
            "Build a reproducible cleaning script and statistical EDA report."
        ),
        "dataset_idea": "Messy real-world CSV from Kaggle/open data (e.g., job postings, property listings, or operations logs).",
        "steps": [
            "Write modular Pandas functions to strip currency/unit symbols, parse mixed timestamps, handle nulls, and flag/cap outliers.",
            "Log before-and-after data quality metrics (row count, null %, duplicate count, outlier count) so reviewers see rigor.",
            "Run summary stats (median vs. mean where skewed, group comparisons, correlation checks) to surface key patterns.",
            "Document assumptions clearly in a `README.md` with sample before/after tables.",
        ],
        "bullet_templates": [
            "Built a reusable Python (Pandas) data-cleaning pipeline that standardized [X,000+] raw records, handled mixed date/currency formats, and cut missing-value errors across [X] columns.",
            "Audited data quality before and after transformation—catching [X] duplicate records and extreme outliers—to prevent skewed summary metrics in downstream analysis.",
            "Conducted exploratory statistical analysis and visual comparisons in Python to surface key segment differences and document reproducible methodology in GitHub.",
        ],
    },
]


def build_resume_bullets(project: dict, metrics: dict[str, str]) -> list[str]:
    bullets = []
    for tpl in project.get("bullet_templates", []):
        text = tpl
        for placeholder, val in metrics.items():
            clean_val = val.strip()
            if clean_val:
                text = text.replace(f"[{placeholder}]", clean_val)
        bullets.append(text)
    return bullets


# --------------------------------------------------------------------------- #
# GitHub README.md / case-study generator
# --------------------------------------------------------------------------- #
README_CONTENT = {
    "proj_retail_sql_bi": {
        "tagline": "Where does gross volume turn into margin leakage? A SQL + BI diagnostic of sales, refunds and returns.",
        "schema": (
            "orders(order_id, customer_id, order_date, status, discount_pct)\n"
            "order_items(order_id, product_id, quantity, unit_price)\n"
            "products(product_id, product_name, category, unit_cost)\n"
            "customers(customer_id, city, segment, signup_date)\n"
            "returns(return_id, order_id, product_id, return_date, refund_amount)"
        ),
        "sql": (
            "WITH item_revenue AS (\n"
            "    SELECT p.category,\n"
            "           SUM(oi.quantity * oi.unit_price) AS gross_revenue,\n"
            "           SUM(oi.quantity * p.unit_cost)   AS cogs\n"
            "    FROM order_items oi\n"
            "    JOIN orders   o ON o.order_id   = oi.order_id\n"
            "    JOIN products p ON p.product_id = oi.product_id\n"
            "    WHERE o.status = 'completed'\n"
            "    GROUP BY p.category\n"
            "), refunds AS (\n"
            "    SELECT p.category, SUM(r.refund_amount) AS refunded\n"
            "    FROM returns r\n"
            "    JOIN products p ON p.product_id = r.product_id\n"
            "    GROUP BY p.category\n"
            ")\n"
            "SELECT i.category,\n"
            "       i.gross_revenue,\n"
            "       COALESCE(f.refunded, 0) AS refunded,\n"
            "       ROUND(100.0 * COALESCE(f.refunded, 0) / i.gross_revenue, 1) AS return_rate_pct,\n"
            "       ROUND(100.0 * (i.gross_revenue - COALESCE(f.refunded, 0) - i.cogs)\n"
            "             / i.gross_revenue, 1) AS net_margin_pct\n"
            "FROM item_revenue i\n"
            "LEFT JOIN refunds f ON f.category = i.category\n"
            "ORDER BY return_rate_pct DESC;"
        ),
        "pandas": (
            "orders = orders.drop_duplicates(subset='order_id')\n"
            "orders['order_date'] = pd.to_datetime(orders['order_date'], errors='coerce')\n"
            "completed = orders[orders['status'].str.lower() == 'completed']\n"
            "monthly = (completed.assign(month=completed['order_date'].dt.to_period('M'))\n"
            "                    .groupby('month', as_index=False)['net_revenue'].sum())"
        ),
        "findings": [
            "{pct} of revenue sits in the highest-return categories, where margin is being eroded.",
            "Net revenue trails gross revenue most visibly in a small set of SKUs and cities across {seg}.",
            "Return-heavy discount tiers lower margin more than they lift volume.",
        ],
        "recommendations": [
            "Tighten free-return thresholds on low-margin, high-return SKUs.",
            "Re-price or bundle the worst-margin products instead of discounting them further.",
            "Track return rate % and net margin % as weekly KPIs on the dashboard.",
        ],
    },
    "proj_churn_retention": {
        "tagline": "Cohort retention and repeat-purchase analysis that pinpoints where new customers stop buying.",
        "schema": (
            "customers(customer_id, signup_date, city, segment)\n"
            "orders(order_id, customer_id, order_date, order_value, status)"
        ),
        "sql": (
            "WITH first_orders AS (\n"
            "    SELECT customer_id,\n"
            "           DATE(MIN(order_date), 'start of month') AS cohort_month\n"
            "    FROM orders\n"
            "    GROUP BY customer_id\n"
            "), activity AS (\n"
            "    SELECT DISTINCT customer_id,\n"
            "           DATE(order_date, 'start of month') AS order_month\n"
            "    FROM orders\n"
            ")\n"
            "SELECT f.cohort_month,\n"
            "       (CAST(strftime('%Y', a.order_month) AS INTEGER) - CAST(strftime('%Y', f.cohort_month) AS INTEGER)) * 12\n"
            "     + (CAST(strftime('%m', a.order_month) AS INTEGER) - CAST(strftime('%m', f.cohort_month) AS INTEGER)) AS month_number,\n"
            "       COUNT(DISTINCT a.customer_id) AS active_customers\n"
            "FROM first_orders f\n"
            "JOIN activity a ON a.customer_id = f.customer_id\n"
            "GROUP BY f.cohort_month, month_number\n"
            "ORDER BY f.cohort_month, month_number;"
        ),
        "pandas": (
            "df['order_month'] = df['order_date'].dt.to_period('M')\n"
            "df['cohort_month'] = df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')\n"
            "df['month_number'] = (df['order_month'] - df['cohort_month']).apply(lambda x: x.n)\n"
            "cohort = (df.groupby(['cohort_month', 'month_number'])['customer_id'].nunique()\n"
            "            .unstack(fill_value=0))\n"
            "retention = cohort.div(cohort[0], axis=0).round(3)"
        ),
        "findings": [
            "Repeat buyers generated {pct} of total revenue despite being a minority of customers.",
            "Most churn happens right after the first order, across {seg} of order history.",
            "Customers who reorder early are far more likely to stay active in later months.",
        ],
        "recommendations": [
            "Launch a post-first-purchase re-engagement flow aimed at the early drop-off window.",
            "Prioritize high-value repeat segments in retention campaigns.",
            "Track 60-day repeat rate as the headline retention KPI.",
        ],
    },
    "proj_messy_pipeline_eda": {
        "tagline": "A reproducible Pandas cleaning pipeline with data-quality logging and a statistical EDA report.",
        "schema": (
            "raw_export(record_id, event_date, amount_text, category, region, quantity, notes)\n"
            "-- Replace with the real columns of your Kaggle / open-data CSV."
        ),
        "sql": "",
        "pandas": (
            "def clean_currency(s: pd.Series) -> pd.Series:\n"
            "    return pd.to_numeric(s.astype(str).str.replace(r'[^0-9.\\-]', '', regex=True), errors='coerce')\n"
            "\n"
            "def cap_outliers(s: pd.Series, k: float = 1.5) -> pd.Series:\n"
            "    q1, q3 = s.quantile([0.25, 0.75])\n"
            "    iqr = q3 - q1\n"
            "    return s.clip(lower=q1 - k * iqr, upper=q3 + k * iqr)\n"
            "\n"
            "df = df.drop_duplicates()\n"
            "df['amount'] = cap_outliers(clean_currency(df['amount_text']))\n"
            "df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')"
        ),
        "findings": [
            "Cleaning removed duplicate records and standardized mixed date/currency formats in {seg}.",
            "Median and mean diverge sharply where outliers were present, so medians are reported.",
            "Missing values clustered in a few columns, so imputation rules are documented per column.",
        ],
        "recommendations": [
            "Validate date and currency formats at the source system to prevent recurring errors.",
            "Schedule the pipeline so refreshed exports are cleaned the same way every time.",
            "Keep the before/after quality log in the repo as proof of rigor.",
        ],
    },
}


def _slugify(text: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    return "-".join(part for part in out.split("-") if part)


def build_readme(project: dict, metrics: dict[str, str] | None = None, author: str = "", skills_line: str = "") -> str:
    """Return a recruiter-grade README.md for the selected project, filled with the user's metrics."""
    metrics = metrics or {}

    def val(key: str, fallback: str) -> str:
        v = str(metrics.get(key, "")).strip()
        return v if v else fallback

    rows = val("rows", "[X,000+] rows")
    pct = val("pct", "[X%]")
    scope = val("scope", "[scope: categories / months / tools]")
    content = README_CONTENT.get(project["id"], {})
    stack = ", ".join(project["stack"])
    repo = _slugify(project["title"])

    findings = [f.format(pct=pct, seg=scope) for f in content.get("findings", [])]
    recs = content.get("recommendations", [])
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(project["steps"], 1))

    approach_parts = []
    if content.get("sql"):
        approach_parts.append("### SQL\n\n```sql\n" + content["sql"] + "\n```")
    if content.get("pandas"):
        approach_parts.append("### Python (Pandas)\n\n```python\n" + content["pandas"] + "\n```")
    approach = "\n\n".join(approach_parts) or "_Add your key queries or code here._"

    lines = [
        f"# {project['title']}",
        "",
        f"> {content.get('tagline', project['business_problem'])}",
        "",
        f"![Stack](https://img.shields.io/badge/stack-{quote_badge(stack)}-1e293b) "
        f"![Status](https://img.shields.io/badge/status-complete-94a3b8)",
        "",
        "## Table of Contents",
        "1. [Business Problem](#business-problem)",
        "2. [Dataset & Schema](#dataset--schema)",
        "3. [Key SQL / Pandas Approach](#key-sql--pandas-approach)",
        "4. [Insights & Recommendations](#insights--recommendations)",
        "5. [Dashboard Preview](#dashboard-preview)",
        "6. [How to Run](#how-to-run)",
        "",
        "## Business Problem",
        "",
        project["business_problem"],
        "",
        f"**Scope:** {scope}  ",
        f"**Stack:** {stack}  ",
        f"**Level:** {project['difficulty']}",
        "",
        "## Dataset & Schema",
        "",
        f"- **Source:** {project['dataset_idea']}  _(add the dataset link here)_",
        f"- **Size:** {rows}",
        "",
        "```text",
        content.get("schema", "[table_name](column_1, column_2, ...)"),
        "```",
        "",
        "**Analysis workflow**",
        "",
        steps,
        "",
        "## Key SQL / Pandas Approach",
        "",
        approach,
        "",
        "## Insights & Recommendations",
        "",
        "### Key findings",
        "",
        *[f"- {f}" for f in findings],
        "",
        "### Recommendations",
        "",
        *[f"{i}. {r}" for i, r in enumerate(recs, 1)],
        "",
        "> Replace bracketed placeholders with the exact numbers from your own analysis before publishing.",
        "",
        "## Dashboard Preview",
        "",
        "![Dashboard preview](images/dashboard-preview.png)",
        "",
        "_Add a 1-page screenshot of your dashboard at `images/dashboard-preview.png` "
        "(KPI cards, a trend chart and one category comparison)._",
        "",
        "## How to Run",
        "",
        "```bash",
        f"git clone https://github.com/<your-username>/{repo}.git",
        f"cd {repo}",
        "pip install pandas jupyter",
        "# 1. Place the dataset in /data",
        "# 2. Run the SQL scripts in /sql or open the notebook in /notebooks",
        "```",
        "",
        "## Repo Structure",
        "",
        "```text",
        f"{repo}/",
        "├── data/            # raw and cleaned datasets (add large files to .gitignore)",
        "├── sql/             # analysis queries",
        "├── notebooks/       # Pandas cleaning and EDA",
        "├── images/          # dashboard-preview.png and charts",
        "└── README.md",
        "```",
        "",
        "## About the Author",
        "",
        f"**{author.strip() or '[Your Name]'}** - aspiring Data Analyst"
        + (f" | Skills: {skills_line}" if skills_line else ""),
        "",
        "[LinkedIn](https://linkedin.com/in/your-handle) · [Portfolio](https://github.com/your-username)",
        "",
    ]
    return "\n".join(lines)


def quote_badge(text: str) -> str:
    """Escape text for a shields.io badge path segment."""
    return text.replace("-", "--").replace("_", "__").replace(" ", "_").replace("/", "%2F").replace(",", "%2C").replace("(", "").replace(")", "")