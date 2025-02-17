import pandas as pd
import sqlite3

# todo:删除第一行id，汉化列名，更新日期格式


def export_to_excel():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM records", conn)
    df.to_excel("QSL.xlsx", index=False)
    conn.close()


if __name__ == "__main__":
    export_to_excel()
