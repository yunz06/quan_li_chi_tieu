from database import get_conn
# Mục đích: Quản lý các danh mục chi tiêu (category)
# Bao gồm thêm, xóa, truy vấn danh mục.
def add_category(name: str) -> bool:
    """
    Thêm một danh mục mới.
    Trả về True nếu thêm thành công hoặc danh mục đã tồn tại (vì dùng INSERT OR IGNORE).
    Trả về False nếu có lỗi hoặc tên trống.
    """
    name = name.strip()
    if not name:
        # Không cho phép tên rỗng
        return False

    conn = get_conn()
    try:
        cur = conn.cursor()

        # INSERT OR IGNORE giúp tránh lỗi nếu tên danh mục đã tồn tại (UNIQUE constraint)
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        conn.commit()

        # Kiểm tra xem tên đó hiện có trong DB chưa (đảm bảo insert thành công hoặc đã tồn tại)
        cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
        return bool(cur.fetchone())
    except Exception:
        # rollback trong trường hợp có lỗi truy vấn (an toàn dữ liệu)
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_category_by_name(name: str) -> bool:
    """
    Xóa danh mục theo tên.
    Nếu danh mục đang được dùng trong bảng expenses, chuyển các khoản chi đó sang 'Khác' thay vì xóa cứng.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Lấy ID của danh mục cần xóa
        cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            # Không tồn tại -> không làm gì
            return False
        del_id = row[0]

        # Đảm bảo danh mục 'Khác' luôn tồn tại để chuyển dữ liệu sang
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Khác')")
        cur.execute("SELECT id FROM categories WHERE name = 'Khác'")
        other_id = cur.fetchone()[0]

        # Chuyển tất cả chi tiêu thuộc danh mục bị xóa sang danh mục 'Khác'
        cur.execute("UPDATE expenses SET category_id = ? WHERE category_id = ?", (other_id, del_id))

        # Xóa danh mục khỏi bảng categories
        cur.execute("DELETE FROM categories WHERE id = ?", (del_id,))
        conn.commit()
        return True

    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_categories() -> list:
    """
    Trả về danh sách tất cả danh mục dưới dạng list[dict]:
    [{"id": 1, "name": "Ăn uống"}, ...]
    Sắp xếp theo ID tăng dần (danh mục mới nhất ở cuối).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY id ASC")
        rows = cur.fetchall()

        # Dùng list comprehension để trả về dữ liệu dễ sử dụng ở giao diện (Tkinter)
        return [{"id": r[0], "name": r[1]} for r in rows]
    finally:
        conn.close()


def get_category_id_by_name(name: str):
    """
    Trả về ID của danh mục theo tên.
    Dùng khi cần chèn chi tiêu mới vào bảng expenses (vì bảng đó lưu ID, không lưu tên).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_category_name_by_id(cat_id: int):
    """
    Trả về tên danh mục theo ID.
    Dùng để hiển thị lại tên danh mục khi truy xuất dữ liệu từ bảng expenses.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()
