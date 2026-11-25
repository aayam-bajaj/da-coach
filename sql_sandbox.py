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
            (5, 'Vikram Joshi', 'Pune', 'Corporate', '2025-04-01');

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
            (1008, 1, 103, 1, '2025-05-01', 'Completed');
    """)
    conn.commit()
    return conn


SQL_CHALLENGES = [
    {
        "title": "Challenge 1: Revenue by City (Joins + Group By)",
        "prompt": "Find total revenue (`quantity * unit_price`) for each customer `city`, counting ONLY `'Completed'` orders. Return columns `city` and `total_revenue`, sorted highest to lowest.",
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
        "title": "Challenge 2: Repeat Buyers (Having + Count)",
        "prompt": "List customer `name` and `completed_orders` count for customers with more than 1 `'Completed'` order.",
        "solution": """
            SELECT c.name, COUNT(o.order_id) AS completed_orders
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.status = 'Completed'
            GROUP BY c.customer_id, c.name
            HAVING COUNT(o.order_id) > 1;
        """,
    },
    {
        "title": "Challenge 3: Top Product per Category (Window Function)",
        "prompt": "Rank products within each `category` by total completed revenue using `RANK() OVER (PARTITION BY ... ORDER BY ...)`. Return `category`, `product_name`, `revenue`, and `rnk`.",
        "solution": """
            SELECT
                p.category,
                p.product_name,
                SUM(o.quantity * p.unit_price) AS revenue,
                RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.quantity * p.unit_price) DESC) AS rnk
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.status = 'Completed'
            GROUP BY p.category, p.product_name;
        """,
    },
]


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

    # Compare values cleanly regardless of column alias casing
    u_norm = user_df.copy()
    s_norm = sol_df.copy()
    u_norm.columns = [c.lower() for c in u_norm.columns]
    s_norm.columns = [c.lower() for c in s_norm.columns]

    is_correct = u_norm.shape == s_norm.shape and u_norm.round(2).equals(s_norm.round(2))
    return user_df, None, is_correct