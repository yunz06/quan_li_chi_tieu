import sqlite3
from pathlib import Path

# Đường dẫn tới file cơ sở dữ liệu SQLite (lưu cùng thư mục với chương trình)
DB_PATH = Path(__file__).parent / "QL_Chi_Tieu.db"

# Hàm trả về một kết nối (connection) đến database.
# Hàm này được dùng ở các module khác để thực hiện truy vấn SQL.
def get_conn():
    return sqlite3.connect(str(DB_PATH))


# Hàm khởi tạo cơ sở dữ liệu: tạo bảng nếu chưa có.
# Dùng khi chương trình khởi động lần đầu (xem file main.py).
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tạo bảng danh mục (categories): lưu tên các loại chi tiêu.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Tạo bảng thu nhập (incomes): lưu thu nhập theo tháng.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL
    )
    """)

    # Tạo bảng chi tiêu (expenses): lưu từng khoản chi, gắn với danh mục.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,               -- ngày theo dạng DD-MM-YYYY
        category_id INTEGER,              -- liên kết với bảng categories
        description TEXT,                 -- mô tả khoản chi
        amount REAL NOT NULL,             -- số tiền chi
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """)

    # Thêm các danh mục mặc định (nếu chưa có)
    defaults = ["Ăn uống", "Đi lại", "Giải trí", "Mua sắm", "Học tập", "Khác"]
    cur.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(d,) for d in defaults])

    conn.commit()
    conn.close()


# Hàm thêm thu nhập: nếu tháng đó đã có, thì cộng dồn thêm.
# Dùng trong giao diện tab "Thu nhập".
def add_income(month: str, amount: float):
    """
    Nếu cùng tháng đã có, cộng dồn; ngược lại insert.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Kiểm tra xem tháng đó đã tồn tại chưa
        cur.execute("SELECT amount FROM incomes WHERE month = ?", (month,))
        row = cur.fetchone()

        if row:
            # Nếu có rồi -> cộng thêm số mới
            new_amount = float(row[0]) + float(amount)
            cur.execute("UPDATE incomes SET amount = ? WHERE month = ?", (new_amount, month))
        else:
            # Nếu chưa có -> thêm dòng mới
            cur.execute("INSERT INTO incomes (month, amount) VALUES (?, ?)", (month, float(amount)))

        conn.commit()
    finally:
        # finally đảm bảo kết nối luôn được đóng, kể cả khi lỗi
        conn.close()


# Lấy số thu nhập theo tháng (định dạng MM-YYYY)
def get_income_for_month(month: str) -> float:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT amount FROM incomes WHERE month = ?", (month,))
        row = cur.fetchone()
        # Nếu có kết quả thì trả về float, nếu không có thì trả về 0.0
        return float(row[0]) if row and row[0] is not None else 0.0
    finally:
        conn.close()


# Lấy toàn bộ danh sách thu nhập, sắp xếp giảm dần theo năm và tháng.
def get_all_incomes():
    """
    Trả về list of (month, amount) sắp xếp theo năm-desc, tháng-desc.
    month lưu là MM-YYYY.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        # substr(month,4,4) -> lấy phần năm (YYYY)
        # substr(month,1,2) -> lấy phần tháng (MM)
        # ORDER BY ... DESC -> sắp xếp mới nhất lên đầu
        cur.execute("""
            SELECT month, amount
            FROM incomes
            ORDER BY substr(month,4,4) DESC, substr(month,1,2) DESC
        """)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()
