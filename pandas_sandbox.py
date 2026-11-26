import numpy as np
import pandas as pd


def get_messy_orders_df() -> pd.DataFrame:
    data = {
        "order_id": [101, 102, 102, 103, 104, 105, 106, 107],
        "customer_city": [
            " mumbai ",
            "Bengaluru",
            "Bengaluru",
            "DELHI",
            "pune",
            None,
            "Mumbai ",
            "bengaluru",
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
        ],
        "quantity": [2, 1, 1, None, 3, 2, 1, 4],
        "order_date": [
            "2025-03-01",
            "04/03/2025",
            "04/03/2025",
            "2025/03/15",
            "18-03-2025",
            "2025-04-02",
            "2025-04-09",
            "invalid_date",
        ],
    }
    return pd.DataFrame(data)


def _check_challenge_1(df: pd.DataFrame):
    # Deduplicate order_id and clean customer_city (title case, stripped, no nulls)
    has_no_dups = "order_id" in df.columns and df["order_id"].nunique() == len(df)
    city_ok = (
        "customer_city" in df.columns
        and df["customer_city"].isna().sum() == 0
        and set(df["customer_city"].astype(str).str.strip().str.title()) >= {"Mumbai", "Bengaluru", "Delhi", "Pune"}
        and (df["customer_city"].astype(str) == df["customer_city"].astype(str).str.strip()).all()
    )
    return has_no_dups and city_ok


def _check_challenge_2(df: pd.DataFrame):
    # Parse raw_price into numeric column `clean_price` and fill missing `quantity` with median/1
    price_col = "clean_price" if "clean_price" in df.columns else ("price" if "price" in df.columns else None)
    price_ok = price_col is not None and pd.api.types.is_numeric_dtype(df[price_col]) and df[price_col].notna().sum() >= 6
    qty_ok = "quantity" in df.columns and pd.api.types.is_numeric_dtype(df["quantity"]) and df["quantity"].isna().sum() == 0
    return price_ok and qty_ok


def _check_challenge_3(df: pd.DataFrame):
    # Parse `order_date` into datetime64
    return "order_date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["order_date"]) and df["order_date"].notna().sum() >= 6


PANDAS_CHALLENGES = [
    {
        "title": "Challenge 1: Deduplicate Orders & Standardize Cities",
        "prompt": (
            "Remove duplicate `order_id` rows (keep first), fill missing `customer_city` with `'Unknown'`, "
            "and strip whitespace + title-case `customer_city` (e.g. `' mumbai '` -> `'Mumbai'`). Assign the result back to `df`."
        ),
        "starter_code": (
            "df = df.drop_duplicates(subset=['order_id'], keep='first').copy()\n"
            "df['customer_city'] = df['customer_city'].fillna('Unknown').str.strip().str.title()"
        ),
        "validator": _check_challenge_1,
        "success_msg": "Clean! Duplicate `order_id`s removed and `customer_city` standardized.",
    },
    {
        "title": "Challenge 2: Parse Currency Strings & Fill Missing Quantities",
        "prompt": (
            "Strip currency symbols (`₹`, `$`, `,`) from `raw_price`, convert to numeric in a new column `clean_price` "
            "(`pd.to_numeric(..., errors='coerce')`), and fill missing `quantity` with `1`. Assign back to `df`."
        ),
        "starter_code": (
            "df = df.copy()\n"
            "cleaned_str = df['raw_price'].astype(str).str.replace(r'[₹$,]', '', regex=True).str.strip()\n"
            "df['clean_price'] = pd.to_numeric(cleaned_str, errors='coerce')\n"
            "df['quantity'] = df['quantity'].fillna(1)"
        ),
        "validator": _check_challenge_2,
        "success_msg": "Nice work! `clean_price` is numeric and `quantity` has zero missing values.",
    },
    {
        "title": "Challenge 3: Convert Mixed Dates to Datetime",
        "prompt": (
            "Convert `order_date` to proper datetime using `pd.to_datetime(df['order_date'], format='mixed', errors='coerce')` "
            "and assign back to `df['order_date']`."
        ),
        "starter_code": (
            "df = df.copy()\n"
            "df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')"
        ),
        "validator": _check_challenge_3,
        "success_msg": "Spot on! `order_date` is now a proper `datetime` column.",
    },
]


def run_pandas_sandbox(user_code: str, challenge: dict):
    df = get_messy_orders_df()
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
    env = {"__builtins__": safe_builtins, "pd": pd, "np": np, "df": df.copy()}

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