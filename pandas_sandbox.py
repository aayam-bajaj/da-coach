import numpy as np
import pandas as pd


def get_messy_orders_df() -> pd.DataFrame:
    data = {
        "order_id": [101, 102, 102, 103, 104, 105, 106, 107, 108],
        "customer_city": [
            " mumbai ",
            "Bengaluru",
            "Bengaluru",
            "DELHI",
            "pune",
            None,
            "Mumbai ",
            "bengaluru",
            "Delhi",
        ],
        "category": [
            "Accessories",
            "Electronics",
            "Electronics",
            "Accessories",
            "Accessories",
            "Electronics",
            "Electronics",
            "Accessories",
            "Electronics",
        ],
        "raw_price": [
            "₹1,200.00",
            "$450.50",
            "$450.50",
            "₹2,500",
            "890.00",
            "₹1,500.75",
            None,
            "₹750.00",
            "₹99,999.00",  # intentional extreme price outlier
        ],
        "quantity": [2, 1, 1, None, 3, 2, 1, 4, 1],
        "order_date": [
            "2025-03-01",
            "04/03/2025",
            "04/03/2025",
            "2025/03/15",
            "18-03-2025",
            "2025-04-02",
            "2025-04-09",
            "invalid_date",
            "2025-05-10",
        ],
    }
    return pd.DataFrame(data)


def _clean_base_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.drop_duplicates(subset=["order_id"], keep="first").copy()
    out["customer_city"] = out["customer_city"].fillna("Unknown").str.strip().str.title()
    cleaned_str = out["raw_price"].astype(str).str.replace(r"[₹$,]", "", regex=True).str.strip()
    out["clean_price"] = pd.to_numeric(cleaned_str, errors="coerce")
    out["quantity"] = out["quantity"].fillna(1)
    out["order_date"] = pd.to_datetime(out["order_date"], format="mixed", errors="coerce")
    return out


def _check_challenge_1(df: pd.DataFrame):
    has_no_dups = "order_id" in df.columns and df["order_id"].nunique() == len(df)
    city_ok = (
        "customer_city" in df.columns
        and df["customer_city"].isna().sum() == 0
        and set(df["customer_city"].astype(str)) >= {"Mumbai", "Bengaluru", "Delhi", "Pune", "Unknown"}
        and (df["customer_city"].astype(str) == df["customer_city"].astype(str).str.strip()).all()
    )
    return has_no_dups and city_ok


def _check_challenge_2(df: pd.DataFrame):
    price_col = "clean_price" if "clean_price" in df.columns else ("price" if "price" in df.columns else None)
    price_ok = price_col is not None and pd.api.types.is_numeric_dtype(df[price_col]) and df[price_col].notna().sum() >= 7
    qty_ok = "quantity" in df.columns and pd.api.types.is_numeric_dtype(df["quantity"]) and df["quantity"].isna().sum() == 0
    return price_ok and qty_ok


def _check_challenge_3(df: pd.DataFrame):
    return (
        "order_date" in df.columns
        and pd.api.types.is_datetime64_any_dtype(df["order_date"])
        and df["order_date"].notna().sum() >= 7
    )


def _check_challenge_4(df: pd.DataFrame):
    # Clean base + cap or filter extreme price > 10000
    if "clean_price" not in df.columns or not pd.api.types.is_numeric_dtype(df["clean_price"]):
        return False
    valid_prices = df["clean_price"].dropna()
    return len(valid_prices) >= 6 and valid_prices.max() <= 10000


def _check_challenge_5(df: pd.DataFrame):
    # Feature engineering: revenue = clean_price * quantity, and order_month string
    rev_ok = "revenue" in df.columns and pd.api.types.is_numeric_dtype(df["revenue"]) and df["revenue"].notna().sum() >= 6
    month_ok = "order_month" in df.columns and df["order_month"].notna().sum() >= 6
    return rev_ok and month_ok


def _check_challenge_6(df: pd.DataFrame):
    # Groupby city summary with total_revenue and order_count
    cols = {c.lower() for c in df.columns}
    return "customer_city" in cols and "total_revenue" in cols and "order_count" in cols and len(df) >= 4


PANDAS_CHALLENGES = [
    {
        "title": "1. [Beginner] Deduplicate Orders & Standardize Cities",
        "prompt": (
            "Remove duplicate `order_id` rows (keep first), fill missing `customer_city` with `'Unknown'`, "
            "and strip whitespace + title-case `customer_city` (e.g. `' mumbai '` -> `'Mumbai'`). Assign back to `df`."
        ),
        "hints": [
            "Chain `.drop_duplicates(subset=['order_id'], keep='first')` first, then `.fillna('Unknown').str.strip().str.title()` on `customer_city`.",
            "Pattern: `df['customer_city'] = df['customer_city'].fillna('Unknown').str.strip().str.title()`",
        ],
        "starter_code": (
            "df = df.drop_duplicates(subset=['order_id'], keep='first').copy()\n"
            "# Clean customer_city below:\n"
        ),
        "solution_code": (
            "df = df.drop_duplicates(subset=['order_id'], keep='first').copy()\n"
            "df['customer_city'] = df['customer_city'].fillna('Unknown').str.strip().str.title()"
        ),
        "success_msg": "Clean! Duplicate `order_id`s removed and `customer_city` standardized.",
        "validator": _check_challenge_1,
    },
    {
        "title": "2. [Beginner] Parse Currency Strings & Fill Missing Quantities",
        "prompt": (
            "Strip currency symbols (`₹`, `$`, `,`) from `raw_price`, convert to numeric in a new column `clean_price` "
            "(`pd.to_numeric(..., errors='coerce')`), and fill missing `quantity` with `1`. Assign back to `df`."
        ),
        "hints": [
            "Use `.astype(str).str.replace(r'[₹$,]', '', regex=True)` before calling `pd.to_numeric(..., errors='coerce')`.",
            "Pattern: `df['clean_price'] = pd.to_numeric(df['raw_price'].astype(str).str.replace(r'[₹$,]', '', regex=True), errors='coerce')`",
        ],
        "starter_code": (
            "df = df.copy()\n"
            "# Parse raw_price into clean_price and fill missing quantity:\n"
        ),
        "solution_code": (
            "df = df.copy()\n"
            "cleaned_str = df['raw_price'].astype(str).str.replace(r'[₹$,]', '', regex=True).str.strip()\n"
            "df['clean_price'] = pd.to_numeric(cleaned_str, errors='coerce')\n"
            "df['quantity'] = df['quantity'].fillna(1)"
        ),
        "success_msg": "Nice work! `clean_price` is numeric and `quantity` has zero missing values.",
        "validator": _check_challenge_2,
    },
    {
        "title": "3. [Beginner] Convert Mixed Dates to Datetime",
        "prompt": (
            "Convert `order_date` to proper datetime using `pd.to_datetime(df['order_date'], format='mixed', errors='coerce')` "
            "so invalid date strings become `NaT` instead of crashing."
        ),
        "hints": [
            "Pass `format='mixed'` and `errors='coerce'` inside `pd.to_datetime(...)`.",
            "Pattern: `df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')`",
        ],
        "starter_code": (
            "df = df.copy()\n"
            "# Convert order_date to datetime64:\n"
        ),
        "solution_code": (
            "df = df.copy()\n"
            "df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')"
        ),
        "success_msg": "Spot on! `order_date` is now a proper `datetime64` column.",
        "validator": _check_challenge_3,
    },
    {
        "title": "4. [Intermediate] Handle Extreme Price Outliers",
        "prompt": (
            "Notice order 108 has `₹99,999.00`. Parse `raw_price` into `clean_price`, then either filter out rows where "
            "`clean_price > 10000` (keeping `NaN` rows if desired) OR cap `clean_price` at `10000` using `.clip(upper=10000)`."
        ),
        "hints": [
            "First create `clean_price` as numeric, then use `df['clean_price'] = df['clean_price'].clip(upper=10000)` or boolean filtering.",
            "Pattern: `df = df[(df['clean_price'] <= 10000) | (df['clean_price'].isna())]`",
        ],
        "starter_code": (
            "df = df.drop_duplicates(subset=['order_id']).copy()\n"
            "df['clean_price'] = pd.to_numeric(df['raw_price'].astype(str).str.replace(r'[₹$,]', '', regex=True), errors='coerce')\n"
            "# Handle extreme outliers (> 10000) below:\n"
        ),
        "solution_code": (
            "df = df.drop_duplicates(subset=['order_id']).copy()\n"
            "df['clean_price'] = pd.to_numeric(df['raw_price'].astype(str).str.replace(r'[₹$,]', '', regex=True), errors='coerce')\n"
            "df['clean_price'] = df['clean_price'].clip(upper=10000)"
        ),
        "success_msg": "Outliers handled cleanly—no extreme spike distorts your averages.",
        "validator": _check_challenge_4,
    },
    {
        "title": "5. [Intermediate] Feature Engineering (`revenue` & `order_month`)",
        "prompt": (
            "Using the pre-cleaned `df` helper (`clean_df` is available), create `df['revenue'] = df['clean_price'] * df['quantity']` "
            "and extract `'YYYY-MM'` into `df['order_month']` using `.dt.to_period('M').astype(str)`."
        ),
        "hints": [
            "`clean_df` is already preloaded in your environment with `clean_price`, `quantity`, and datetime `order_date`.",
            "Pattern: `df = clean_df.copy(); df['revenue'] = df['clean_price'] * df['quantity']; df['order_month'] = df['order_date'].dt.to_period('M').astype(str)`",
        ],
        "starter_code": (
            "df = clean_df.copy()\n"
            "# Create revenue and order_month columns:\n"
        ),
        "solution_code": (
            "df = clean_df.copy()\n"
            "df['revenue'] = df['clean_price'] * df['quantity']\n"
            "df['order_month'] = df['order_date'].dt.to_period('M').astype(str)"
        ),
        "success_msg": "Great! `revenue` and `order_month` features are ready for time-series analysis.",
        "validator": _check_challenge_5,
    },
    {
        "title": "6. [Advanced] City KPI Summary (`groupby` + `agg`)",
        "prompt": (
            "Starting from `clean_df`, compute `revenue = clean_price * quantity`, cap `clean_price` at `10000` first, "
            "and group by `customer_city` to produce columns `customer_city`, `total_revenue`, and `order_count` (sorted by `total_revenue` desc). Assign the summary table to `df`."
        ),
        "hints": [
            "Use `.groupby('customer_city', as_index=False).agg(total_revenue=('revenue', 'sum'), order_count=('order_id', 'count'))`.",
            "Pattern: `df = df.groupby('customer_city', as_index=False).agg(total_revenue=('revenue', 'sum'), order_count=('order_id', 'count')).sort_values('total_revenue', ascending=False)`",
        ],
        "starter_code": (
            "df = clean_df.copy()\n"
            "df['clean_price'] = df['clean_price'].clip(upper=10000)\n"
            "df['revenue'] = df['clean_price'] * df['quantity']\n"
            "# Group by customer_city into total_revenue and order_count:\n"
        ),
        "solution_code": (
            "df = clean_df.copy()\n"
            "df['clean_price'] = df['clean_price'].clip(upper=10000)\n"
            "df['revenue'] = df['clean_price'] * df['quantity']\n"
            "df = (\n"
            "    df.groupby('customer_city', as_index=False)\n"
            "    .agg(total_revenue=('revenue', 'sum'), order_count=('order_id', 'count'))\n"
            "    .sort_values('total_revenue', ascending=False)\n"
            ")"
        ),
        "success_msg": "Executive-ready KPI summary table built!",
        "validator": _check_challenge_6,
    },
]


def run_pandas_sandbox(user_code: str, challenge: dict):
    raw_df = get_messy_orders_df()
    clean_df = _clean_base_df(raw_df)
    safe_builtins = {
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "abs": abs,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "range": range,
        "isinstance": isinstance,
    }
    env = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "np": np,
        "df": raw_df.copy(),
        "clean_df": clean_df.copy(),
    }

    try:
        exec(user_code, env)
        result_df = env.get("df")
        if not isinstance(result_df, pd.DataFrame):
            return None, None, "Make sure `df` remains a pandas DataFrame.", False

        null_summary = result_df.isna().sum().to_dict()
        passed = bool(challenge["validator"](result_df))
        return result_df, null_summary, None, passed
    except Exception as e:
        return None, None, f"Pandas Error: {e}", False