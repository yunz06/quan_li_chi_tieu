import database
from giao_dien import open_giao_dien

if __name__ == "__main__":
    database.init_db()
    open_giao_dien()