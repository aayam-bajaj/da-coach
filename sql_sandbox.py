import sqlite3
import pandas as pd


def init_sandbox_db():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            segment TEXT,
            signup_date TEXT
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            unit_price REAL
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date TEXT,
            status TEXT
        );

        INSERT INTO customers VALUES
            (1, 'Aarav Sharma', 'Mumbai', 'Consumer', '2025-01-12'),
            (2, 'Priya Nair', 'Bengaluru', 'Corporate', '2025-02-05'),
            (3, 'Rohan Verma', 'Delhi', 'Consumer', '2025-02-19'),
            (4, 'Sneha Iyer', 'Mumbai', 'Home Office', '2025-03-10'),
            (5, 'Vikram Joshi', 'Pune', 'Corporate', '2025-04-01'),
            (6, 'Ananya Kulkarni', 'Bengaluru', 'Consumer', '2025-04-12');

        INSERT INTO products VALUES
            (101, 'Laptop Stand', 'Accessories', 45.00),
            (102, 'Mechanical Keyboard', 'Accessories', 120.00),
            (103, '27-inch Monitor', 'Electronics', 320.00),
            (104, 'USB-C Hub', 'Accessories', 35.00),
            (105, 'Noise-Canceling Headphones', 'Electronics', 210.00);

        INSERT INTO orders VALUES
            (1001, 1, 102, 1, '2025-03-01', 'Completed'),
            (1002, 2, 103, 2, '2025-03-04', 'Completed'),
            (1003, 1, 104, 2, '2025-03-15', 'Completed'),
            (1004, 3, 105, 1, '2025-03-18', 'Cancelled'),
            (1005, 2, 101, 3, '2025-04-02', 'Completed'),
            (1006, 4, 103, 1, '2025-04-09', 'Completed'),
            (1007, 5, 105, 2, '2025-04-14', 'Completed'),
            (1008, 1, 103, 1, '2025-05-01', 'Completed'),
            (1009, 2, 102, 2, '2025-05-11', 'Completed');
    """)
    conn.commit()
    return conn


SQL_CHALLENGES = [
    {
        "title": "1. [Beginner] Revenue by City (Joins + Group By)",
        "prompt": "Find total revenue (`quantity * unit_price`) for each customer `city`, counting ONLY `'Completed'` orders. Return columns `city` and `total_revenue`, sorted highest to lowest.",
        "hints": [
            "Join `orders` with both `customers` (for `city`) and `products` (for `unit_price`), then filter `WHERE o.status = 'Completed'`.",
            "Pattern: `SELECT c.city, SUM(o.quantity * p.unit_price) AS total_revenue FROM orders o JOIN ... GROUP BY c.city ORDER BY total_revenue DESC`",
        ],
        "solution": """
            SELECT c.city, SUM(o.quantity * p.unit_price) AS total_revenue
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN products p ON o.product_id = p.product_id
            WHERE o.status = 'Completed'
            GROUP BY c.city
            ORDER BY total_revenue DESC;
        """,
    },
    {
        "title": "2. [Beginner] Repeat Buyers (HAVING + COUNT)",
        "prompt": "List customer `name` and `completed_orders` count for customers with more than 1 `'Completed'` order. Sort by `completed_orders` descending.",
        "hints": [
            "Filter `WHERE o.status = 'Completed'` BEFORE grouping, then use `HAVING` on `COUNT(o.order_id)`.",
            "Pattern: `SELECT c.name, COUNT(o.order_id) AS completed_orders FROM customers c JOIN orders o ON ... WHERE o.status = 'Completed' GROUP BY c.customer_id, c.name HAVING COUNT(o.order_id) > 1 ORDER BY completed_orders DESC`",
        ],
        "solution": """
            SELECT c.name, COUNT(o.order_id) AS completed_orders
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.status = 'Completed'
            GROUP BY c.customer_id, c.name
            HAVING COUNT(o.order_id) > 1
            ORDER BY completed_orders DESC;
        """,
    },
    {
        "title": "3. [Intermediate] Zero-Order Customers (LEFT JOIN + NULL)",
        "prompt": "Find customers who have NEVER placed a `'Completed'` order (including customers with no orders or only cancelled orders). Return `customer_id` and `name`, ordered by `customer_id`.",
        "hints": [
            "Put `o.status = 'Completed'` inside the `LEFT JOIN ... ON` condition (not in `WHERE`, which would turn it into an `INNER JOIN`).",
            "Pattern: `SELECT c.customer_id, c.name FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'Completed' WHERE o.order_id IS NULL ORDER BY c.customer_id`",
        ],
        "solution": """
            SELECT c.customer_id, c.name
            FROM customers c
            LEFT JOIN orders o
                ON c.customer_id = o.customer_id
                AND o.status = 'Completed'
            WHERE o.order_id IS NULL
            ORDER BY c.customer_id;
        """,
    },
    {
        "title": "4. [Intermediate] Customer Value Tiers (CASE WHEN)",
        "prompt": "Classify each customer with at least 1 completed order into `tier`: `'VIP'` if total completed spend >= 700, `'Regular'` if >= 300, else `'Starter'`. Return `name`, `total_spend`, and `tier`, sorted by `total_spend` descending.",
        "hints": [
            "Compute `SUM(o.quantity * p.unit_price)` per customer first, then wrap that aggregate inside a `CASE WHEN` expression.",
            "Pattern: `CASE WHEN SUM(...) >= 700 THEN 'VIP' WHEN SUM(...) >= 300 THEN 'Regular' ELSE 'Starter' END AS tier`",
        ],
        "solution": """
            SELECT
                c.name,
                SUM(o.quantity * p.unit_price) AS total_spend,
                CASE
                    WHEN SUM(o.quantity * p.unit_price) >= 700 THEN 'VIP'
                    WHEN SUM(o.quantity * p.unit_price) >= 300 THEN 'Regular'
                    ELSE 'Starter'
                END AS tier
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN products p ON o.product_id = p.product_id
            WHERE o.status = 'Completed'
            GROUP BY c.customer_id, c.name
            ORDER BY total_spend DESC;
        """,
    },
    {
        "title": "5. [Advanced] Top Product per Category (Window RANK)",
        "prompt": "Rank products within each `category` by total completed revenue using `RANK() OVER (PARTITION BY ... ORDER BY ...)`. Return `category`, `product_name`, `revenue`, and `rnk`, ordered by `category`, `rnk`.",
        "hints": [
            "Group by `p.category, p.product_name` first so `SUM(o.quantity * p.unit_price)` is calculated per product, then apply `RANK() OVER (...)` on that sum.",
            "Pattern: `RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.quantity * p.unit_price) DESC) AS rnk`",
        ],
        "solution": """
            SELECT
                p.category,
                p.product_name,
                SUM(o.quantity * p.unit_price) AS revenue,
                RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.quantity * p.unit_price) DESC) AS rnk
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.status = 'Completed'
            GROUP BY p.category, p.product_name
            ORDER BY p.category, rnk;
        """,
    },
    {
        "title": "6. [Advanced] Month-over-Month Revenue & Previous Month (CTE + LAG)",
        "prompt": "Using a CTE for monthly completed revenue (`substr(o.order_date, 1, 7)` as `order_month`), return `order_month`, `monthly_revenue`, and `prev_month_revenue` using `LAG()`, ordered by `order_month`.",
        "hints": [
            "In SQLite, extract `'YYYY-MM'` with `substr(o.order_date, 1, 7)` inside a CTE `monthly_sales`, then select `LAG(monthly_revenue) OVER (ORDER BY order_month)`.",
            "Pattern: `WITH monthly_sales AS (SELECT substr(o.order_date, 1, 7) AS order_month, SUM(...) AS monthly_revenue FROM ... GROUP BY 1) SELECT order_month, monthly_revenue, LAG(monthly_revenue) OVER (ORDER BY order_month) AS prev_month_revenue FROM monthly_sales`",
        ],
        "solution": """
            WITH monthly_sales AS (
                SELECT
                    substr(o.order_date, 1, 7) AS order_month,
                    SUM(o.quantity * p.unit_price) AS monthly_revenue
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.status = 'Completed'
                GROUP BY substr(o.order_date, 1, 7)
            )
            SELECT
                order_month,
                monthly_revenue,
                LAG(monthly_revenue) OVER (ORDER BY order_month) AS prev_month_revenue
            FROM monthly_sales
            ORDER BY order_month;
        """,
    },
]


def get_expected_preview(solution_sql: str) -> pd.DataFrame:
    conn = init_sandbox_db()
    try:
        return pd.read_sql_query(solution_sql.strip().rstrip(";"), conn)
    finally:
        conn.close()


def execute_and_grade(user_sql: str, solution_sql: str):
    cleaned = user_sql.strip().rstrip(";")
    if not cleaned.lower().startswith(("select", "with")):
        return None, "Only SELECT or WITH (CTE) queries are allowed in the sandbox.", False

    conn = init_sandbox_db()
    try:
        user_df = pd.read_sql_query(cleaned, conn)
        sol_df = pd.read_sql_query(solution_sql.strip().rstrip(";"), conn)
    except Exception as e:
        return None, f"SQL Error: {e}", False
    finally:
        conn.close()

    u_norm = user_df.copy()
    s_norm = sol_df.copy()
    u_norm.columns = [c.lower() for c in u_norm.columns]
    s_norm.columns = [c.lower() for c in s_norm.columns]

    is_correct = u_norm.shape == s_norm.shape and u_norm.round(2).equals(s_norm.round(2))
    return user_df, None, is_correct