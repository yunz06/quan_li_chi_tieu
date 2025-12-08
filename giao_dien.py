import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re

# Import các module xử lý dữ liệu
import database
import danh_muc
import chi_tieu
import xuat_excel

# HÀM TIỆN ÍCH KIỂM TRA VÀ XỬ LÝ CHUỖI
def valid_month_format(s: str) -> bool:
    if not s:
        return False
    return bool(re.fullmatch(r"(0[1-9]|1[0-2])-\d{4}", s.strip()))

def current_month_str() -> str:
    return datetime.now().strftime("%m-%Y")

def safe_export_to_excel(month: str):
    try:
        return xuat_excel.export_to_excel(month)
    except TypeError:
        return xuat_excel.export_to_excel()

# GIAO DIỆN CHÍNH CỦA ỨNG DỤNG
def open_giao_dien():
    # 1. TẠO CỬA SỔ CHÍNH
    root = tk.Tk()
    root.title("💰 QUẢN LÝ CHI TIÊU CÁ NHÂN 💰")
    root.geometry("1180x800")      # Kích thước cửa sổ ban đầu
    root.minsize(980, 620)         # Giới hạn thu nhỏ
    root.configure(bg="#1e1e1e")   # Màu nền tối để dễ nhìn

    # 2. ĐỊNH NGHĨA MÀU SẮC & STYLE CHUNG
    BG = "#1e1e1e"
    FG = "#f4f4f4"
    HEADER = "#433029"
    ACCENT = "#d4a15f"
    ACTIVE_TAB_BG = "#f2c28a"
    ACTIVE_TAB_FG = "#000000"
    INACTIVE_TAB_BG = "#d4a15f"
    INACTIVE_TAB_FG = "#111111"

    # 3. CẤU HÌNH GIAO DIỆN THEO THEME
    style = ttk.Style()
    try:
        style.theme_use("clam")  # giao diện đẹp, phổ biến cho ttk
    except Exception:
        pass

    # Cấu hình style cơ bản
    style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 11))
    style.configure("Header.TLabel", background=HEADER, foreground=FG, font=("Segoe UI Semibold", 14))
    style.configure("TButton", background=ACCENT, foreground="#000000", padding=6)
    style.map("TButton", background=[("active", "#f0be7a")])
    style.configure("TEntry", fieldbackground="#2f2d2c", foreground=FG)
    style.configure("TCombobox", fieldbackground="#2f2d2c", foreground=FG)
    style.configure("Treeview", background="#262424", foreground=FG, fieldbackground="#262424", rowheight=26)
    style.configure("Treeview.Heading", background=HEADER, foreground=FG, font=("Segoe UI Semibold", 11))
    style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"),
                    padding=[10, 6],
                    background=INACTIVE_TAB_BG, foreground=INACTIVE_TAB_FG)
    style.map("TNotebook.Tab", background=[("selected", ACTIVE_TAB_BG)], foreground=[("selected", ACTIVE_TAB_FG)])

    # 4. TIÊU ĐỀ ỨNG DỤNG
    ttk.Label(root, text="📊  QUẢN LÝ CHI TIÊU CÁ NHÂN", style="Header.TLabel").pack(fill="x", pady=6)

    # 5. TẠO KHUNG GIAO DIỆN CHÍNH (Notebook - gồm nhiều tab)
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=8, pady=8)

    # TAB 1: THU NHẬP
    tab_income = ttk.Frame(notebook)
    notebook.add(tab_income, text="Thu nhập")

    # Label + Entry để nhập dữ liệu
    ttk.Label(tab_income, text="Tháng (MM-YYYY):").grid(row=0, column=0, padx=12, pady=8, sticky="e")
    month_in = ttk.Entry(tab_income, width=18)
    month_in.insert(0, current_month_str())  # tự động gợi ý tháng hiện tại
    month_in.grid(row=0, column=1, sticky="w")

    ttk.Label(tab_income, text="Thu nhập (VND):").grid(row=1, column=0, padx=12, pady=8, sticky="e")
    income_e = ttk.Entry(tab_income, width=20)
    income_e.grid(row=1, column=1, sticky="w")

    # Khi người dùng nhấn “Lưu thu nhập”
    def save_income():
        m = month_in.get().strip()
        if not valid_month_format(m):
            messagebox.showerror("Lỗi", "Định dạng tháng không hợp lệ (MM-YYYY).")
            return
        try:
            v = float(income_e.get())
        except Exception:
            messagebox.showerror("Lỗi", "Số tiền không hợp lệ.")
            return
        try:
            database.add_income(m, v)  # gọi hàm trong database.py
        except Exception as e:
            print("Lỗi khi lưu thu nhập:", e)
            messagebox.showerror("Lỗi", "Không lưu được thu nhập.")
            return
        messagebox.showinfo("Thành công", f"Đã lưu/cộng dồn thu nhập tháng {m}.")
        income_e.delete(0, tk.END)
        load_incomes()
        refresh_if_stats_visible()

    ttk.Button(tab_income, text="💾 Lưu thu nhập", command=save_income).grid(row=2, column=1, pady=8, sticky="w")

    # Treeview để hiển thị danh sách thu nhập
    income_tree = ttk.Treeview(tab_income, columns=("Tháng", "Số tiền"), show="headings", height=10)
    income_tree.heading("Tháng", text="Tháng")
    income_tree.heading("Số tiền", text="Số tiền (VND)")
    income_tree.column("Tháng", width=140, anchor="center")
    income_tree.column("Số tiền", width=240, anchor="e")
    income_tree.grid(row=3, column=0, columnspan=3, padx=12, pady=10, sticky="nsew")

    # Hàm tải dữ liệu thu nhập lên bảng
    def load_incomes():
        income_tree.delete(*income_tree.get_children())
        try:
            for m, a in database.get_all_incomes():
                income_tree.insert("", "end", values=(m, f"{float(a):,.0f}"))
        except Exception as e:
            print("Lỗi load_incomes:", e)

    # TAB 2: CHI TIÊU
    tab_exp = ttk.Frame(notebook)
    notebook.add(tab_exp, text="Chi tiêu")

    # --- Các ô nhập liệu cơ bản ---
    ttk.Label(tab_exp, text="Danh mục:").grid(row=0, column=0, padx=12, pady=8, sticky="e")
    cat_vals = [c["name"] for c in danh_muc.get_all_categories()]
    cat_var = tk.StringVar(value=cat_vals[0] if cat_vals else "")
    cat_cb = ttk.Combobox(tab_exp, textvariable=cat_var, values=cat_vals, width=40)
    cat_cb.grid(row=0, column=1, padx=8, pady=8, sticky="w")

    ttk.Label(tab_exp, text="Mô tả:").grid(row=1, column=0, padx=12, pady=8, sticky="e")
    desc_e = ttk.Entry(tab_exp, width=52)
    desc_e.grid(row=1, column=1, padx=8, pady=8, sticky="w")

    ttk.Label(tab_exp, text="Số tiền (VND):").grid(row=2, column=0, padx=12, pady=8, sticky="e")
    amt_e = ttk.Entry(tab_exp, width=28)
    amt_e.grid(row=2, column=1, padx=8, pady=8, sticky="w")

    ttk.Label(tab_exp, text="Ngày (DD-MM-YYYY):").grid(row=3, column=0, padx=12, pady=8, sticky="e")
    date_e = ttk.Entry(tab_exp, width=28)
    date_e.insert(0, datetime.now().strftime("%d-%m-%Y"))
    date_e.grid(row=3, column=1, padx=8, pady=8, sticky="w")

    # Cập nhật danh mục khi có thêm mới
    def refresh_cat_cb():
        vals = [c["name"] for c in danh_muc.get_all_categories()]
        cat_cb["values"] = vals
        stats_cat_cb["values"] = vals
        if vals:
            if not cat_var.get():
                cat_var.set(vals[0])
            if not stats_cat_cb.get():
                stats_cat_cb.set(vals[0])

    # Thêm chi tiêu
    def save_expense():
        name = cat_var.get()
        if not name:
            messagebox.showerror("Lỗi", "Vui lòng chọn danh mục!")
            return
        cid = danh_muc.get_category_id_by_name(name)
        desc = desc_e.get().strip()
        try:
            val = float(amt_e.get())
        except Exception:
            messagebox.showerror("Lỗi", "Số tiền không hợp lệ!")
            return
        date = date_e.get().strip()
        try:
            chi_tieu.add_expense(date, cid, desc, val)
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
            return
        messagebox.showinfo("Thành công", "Đã thêm chi tiêu!")
        desc_e.delete(0, tk.END)
        amt_e.delete(0, tk.END)
        refresh_if_stats_visible()

    ttk.Button(tab_exp, text="💾 Lưu", command=save_expense).grid(row=4, column=1, padx=8, pady=10, sticky="w")

    # TAB 3: DANH MỤC CHI TIÊU
    tab_cat = ttk.Frame(notebook)
    notebook.add(tab_cat, text="Danh mục")

    # Nhập tên danh mục mới
    ttk.Label(tab_cat, text="Tên danh mục mới:").pack(pady=8)
    new_cat_entry = ttk.Entry(tab_cat, width=50)
    new_cat_entry.pack(pady=4)

    # Nút thêm danh mục
    def add_category():
        nm = new_cat_entry.get().strip()
        if not nm:
            messagebox.showerror("Lỗi", "Tên danh mục không được trống!")
            return
        ok = danh_muc.add_category(nm)
        if ok:
            messagebox.showinfo("Thành công", f"Đã thêm danh mục '{nm}'!")
            new_cat_entry.delete(0, tk.END)
            load_categories()
            refresh_cat_cb()
        else:
            messagebox.showwarning("Lỗi", "Không thể thêm (có thể đã tồn tại).")

    ttk.Button(tab_cat, text="➕ Thêm danh mục", command=add_category).pack(pady=6)

    # Bảng hiển thị danh mục
    cat_tree = ttk.Treeview(tab_cat, columns=("STT", "Tên"), show="headings", height=12)
    cat_tree.heading("STT", text="STT")
    cat_tree.heading("Tên", text="Tên danh mục")
    cat_tree.column("STT", width=60, anchor="center")
    cat_tree.column("Tên", width=420, anchor="w")
    cat_tree.pack(padx=10, pady=10, fill="both", expand=True)

    def load_categories():
        """Nạp lại danh sách danh mục."""
        cat_tree.delete(*cat_tree.get_children())
        cats = danh_muc.get_all_categories()
        for idx, c in enumerate(cats, start=1):
            cat_tree.insert("", "end", values=(idx, c["name"]))

    # Xóa danh mục
    def delete_selected_category():
        sel = cat_tree.selection()
        if not sel:
            messagebox.showerror("Lỗi", "Vui lòng chọn danh mục để xóa!")
            return
        cat_name = cat_tree.item(sel[0], "values")[1]
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa danh mục '{cat_name}'?"):
            if danh_muc.delete_category_by_name(cat_name):
                messagebox.showinfo("Thành công", f"Đã xóa '{cat_name}'.")
                load_categories()
                refresh_cat_cb()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa danh mục (đang được sử dụng).")

    ttk.Button(tab_cat, text="🗑️ Xóa danh mục đã chọn", command=delete_selected_category).pack(pady=6)

    # TAB 4: THỐNG KÊ
    tab_stats = ttk.Frame(notebook)
    notebook.add(tab_stats, text="Thống kê")
    stats_index = notebook.index("end") - 1

    # --- Khu điều khiển ---
    ctrl_top = ttk.Frame(tab_stats)
    ctrl_top.pack(fill="x", padx=10, pady=(8,4))
    ttk.Label(ctrl_top, text="Chế độ:").grid(row=0, column=0, padx=6, sticky="e")
    mode_var = tk.StringVar(value="Theo tháng")
    mode_cb = ttk.Combobox(ctrl_top, textvariable=mode_var, values=["Theo tháng", "Theo danh mục"], width=20, state="readonly")
    mode_cb.grid(row=0, column=1, padx=6, sticky="w")

    # --- Các ô nhập cho thống kê ---
    ctrl_bot = ttk.Frame(tab_stats)
    ctrl_bot.pack(fill="x", padx=10, pady=(4,8))
    ttk.Label(ctrl_bot, text="Tháng (MM-YYYY):").grid(row=0, column=0, padx=6, sticky="e")
    stats_month_e = ttk.Entry(ctrl_bot, width=14)
    stats_month_e.insert(0, current_month_str())
    stats_month_e.grid(row=0, column=1, sticky="w")
    ttk.Label(ctrl_bot, text="Danh mục:").grid(row=0, column=2, padx=6, sticky="e")
    stats_cat_cb = ttk.Combobox(ctrl_bot, values=[c["name"] for c in danh_muc.get_all_categories()], width=30)
    stats_cat_cb.grid(row=0, column=3, sticky="w")

    # Các nút chức năng
    ttk.Button(ctrl_bot, text="📊 Thống kê", command=lambda: update_stats_display(True)).grid(row=0, column=5, padx=6)
    ttk.Button(ctrl_bot, text="📈 Xuất Excel", command=lambda: export_excel()).grid(row=0, column=6, padx=6)

    summary_label = ttk.Label(tab_stats, text="", font=("Segoe UI Semibold", 11))
    summary_label.pack(pady=6)

    # Treeview hiển thị kết quả thống kê
    detail_cols = ("STT", "Danh mục", "Mô tả", "Số tiền", "Ngày")
    detail_tree = ttk.Treeview(tab_stats, columns=detail_cols, show="headings", height=14)
    for c in detail_cols:
        detail_tree.heading(c, text=c, anchor="center")
        detail_tree.column(c, width=160, anchor="center")
    detail_tree.column("STT", width=60, anchor="center")
    detail_tree.column("Số tiền", anchor="e")
    detail_tree.pack(fill="both", expand=True, padx=8, pady=6)

    # HÀM BÊN TRONG TAB THỐNG KÊ
    def clear_detail():
        detail_tree.delete(*detail_tree.get_children())
        summary_label.config(text="")

    def update_stats_display(user_pressed=False):
        """
        Cập nhật dữ liệu thống kê:
        - Nếu chế độ 'Theo tháng': hiển thị thu nhập, chi tiêu, số dư
        - Nếu 'Theo danh mục': hiển thị tổng chi từng loại
        """
        mode = mode_var.get()
        month = stats_month_e.get().strip()
        cat = stats_cat_cb.get().strip()

        if mode == "Theo tháng":
            # Gọi database + chi_tieu để lấy dữ liệu tháng đó
            try:
                inc = database.get_income_for_month(month)
                spent = chi_tieu.get_total_expense_by_month(month)
            except Exception:
                inc = spent = 0
            bal = inc - spent
            summary_label.config(text=f"Tháng {month} | Thu nhập: {inc:,.0f} | Đã chi: {spent:,.0f} | Số dư: {bal:,.0f}")

            detail_tree.delete(*detail_tree.get_children())
            conn = database.get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(c.name,'Khác') AS category, e.description, e.amount, e.date
                FROM expenses e LEFT JOIN categories c ON e.category_id = c.id
                WHERE substr(e.date,4,7) = ?
                ORDER BY substr(e.date,7,4) DESC, substr(e.date,4,2) DESC, substr(e.date,1,2) DESC, e.id DESC
            """, (month,))
            rows = cur.fetchall()
            conn.close()

            for i, (category, desc, amt, date) in enumerate(rows, start=1):
                detail_tree.insert("", "end", values=(i, category, desc, f"{amt:,.0f}", date))

            # Cảnh báo nếu vượt 90%
            if inc > 0 and spent/inc > 0.9 and user_pressed:
                messagebox.showwarning("⚠️ Cảnh báo", f"Chi tiêu tháng {month} đã vượt {(spent/inc):.0%} thu nhập!")

        else:
            # Theo danh mục
            if not cat:
                # Không chọn danh mục => tổng hợp tất cả
                conn = database.get_conn()
                cur = conn.cursor()
                cur.execute("""
                    SELECT COALESCE(c.name,'Khác') AS category, SUM(e.amount)
                    FROM expenses e LEFT JOIN categories c ON e.category_id = c.id
                    GROUP BY category
                    ORDER BY SUM(e.amount) DESC
                """)
                rows = cur.fetchall()
                conn.close()
                summary_label.config(text="Tổng hợp chi tiêu theo danh mục")
                detail_tree.delete(*detail_tree.get_children())
                for i, (category, total) in enumerate(rows, start=1):
                    detail_tree.insert("", "end", values=(i, category, "", f"{total:,.0f}", ""))
            else:
                # Nếu chọn danh mục cụ thể
                conn = database.get_conn()
                cur = conn.cursor()
                cur.execute("""
                    SELECT COALESCE(c.name,'Khác'), e.description, e.amount, e.date
                    FROM expenses e LEFT JOIN categories c ON e.category_id = c.id
                    WHERE COALESCE(c.name,'Khác') = ?
                    ORDER BY substr(e.date,7,4) DESC
                """, (cat,))
                rows = cur.fetchall()
                conn.close()
                total = sum(r[2] for r in rows)
                summary_label.config(text=f"Danh mục '{cat}' - Tổng chi: {total:,.0f} VND")
                detail_tree.delete(*detail_tree.get_children())
                for i, (category, desc, amt, date) in enumerate(rows, start=1):
                    detail_tree.insert("", "end", values=(i, category, desc, f"{amt:,.0f}", date))

    # Nút xuất Excel
    def export_excel():
        m = stats_month_e.get().strip() or current_month_str()
        if not valid_month_format(m):
            messagebox.showerror("Lỗi", "Định dạng tháng không hợp lệ (MM-YYYY).")
            return
        inc = database.get_income_for_month(m)
        spent = chi_tieu.get_total_expense_by_month(m)
        if (inc == 0) and (spent == 0):
            messagebox.showinfo("Không có dữ liệu", f"Tháng {m} không có dữ liệu để xuất.")
            return
        safe_export_to_excel(m)
        messagebox.showinfo("Thành công", f"Đã xuất file Excel tháng {m} trong thư mục chương trình.")

    # CÁC HÀM HỖ TRỢ KHỞI TẠO
    def refresh_if_stats_visible():
        if notebook.index("current") == stats_index:
            update_stats_display(False)

    def initial_load():
        load_incomes()
        load_categories()
        refresh_cat_cb()
        update_stats_display(False)

    initial_load()
    root.mainloop()