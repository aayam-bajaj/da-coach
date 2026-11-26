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