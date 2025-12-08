from database import get_conn, get_income_for_month
from datetime import datetime
from tkinter import messagebox

# Các hàm quản lý chi tiêu (expenses): thêm, xóa, sửa, thống kê, cảnh báo.

def add_expense(date_str: str, category_id: int, description: str, amount: float):
    """
    Thêm một khoản chi tiêu mới.
    - Kiểm tra định dạng ngày DD-MM-YYYY
    - Lưu dữ liệu vào DB
    - Sau khi thêm, tự động kiểm tra cảnh báo vượt 90% thu nhập tháng đó.
    """
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        raise ValueError("Định dạng ngày phải là DD-MM-YYYY")

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (date, category_id, description, amount) VALUES (?, ?, ?, ?)",
            (date_str, category_id, description or "", float(amount))
        )
        conn.commit()
    finally:
        conn.close()

    month = dt.strftime("%m-%Y")
    check_budget_alert_for_month(month)

def get_all_expenses():
    """Trả về danh sách tất cả chi tiêu (id, danh mục, mô tả, số tiền, ngày)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Sử dụng substr để sắp xếp theo năm -> tháng -> ngày -> id
        cur.execute("""
            SELECT e.id, COALESCE(c.name, 'Khác') as category, e.description, e.amount, e.date
            FROM expenses e LEFT JOIN categories c ON e.category_id = c.id
            ORDER BY substr(e.date,7,4) DESC, substr(e.date,4,2) DESC, substr(e.date,1,2) DESC, e.id DESC
        """)
        rows = cur.fetchall()
        return [(r[0], r[1], r[2], r[3], r[4]) for r in rows]
    finally:
        conn.close()

def get_expense_by_category():
    """Tổng hợp chi tiêu theo từng danh mục."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(c.name,'Khác') AS category, SUM(e.amount) AS total
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            GROUP BY category
            ORDER BY total DESC
        """)
        return cur.fetchall()
    finally:
        conn.close()

def get_total_expense_by_month(month: str) -> float:
    """Tính tổng chi của một tháng (MM-YYYY)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT SUM(amount) FROM expenses WHERE substr(date,4,7) = ?", (month,))
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
    finally:
        conn.close()

def get_expense_summary_by_category_month(month: str):
    """Tổng hợp chi theo danh mục trong một tháng."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(c.name,'Khác') AS category, SUM(e.amount) AS total
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE substr(e.date,4,7) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (month,))
        return cur.fetchall()
    finally:
        conn.close()

def check_budget_alert_for_month(month: str):
    """
    Sau khi thêm chi tiêu, kiểm tra xem tổng chi tháng đó
    có vượt 90% thu nhập hay không. Nếu có -> cảnh báo.
    """
    total = get_total_expense_by_month(month)
    income = get_income_for_month(month)
    if income <= 0:
        return
    ratio = total / income
    if ratio > 0.9:
        messagebox.showwarning(
            "⚠️ Cảnh báo vượt 90% thu nhập",
            f"Tổng chi tiêu tháng {month}: {total:,.0f} VND\n"
            f"Thu nhập: {income:,.0f} VND\nTỉ lệ: {ratio:.0%}"
        )
