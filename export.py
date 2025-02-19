import pandas as pd
import sqlite3


def export_to_excel():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM records", conn)
    print(df)
    df.drop("id", axis=1, inplace=True)
    df.columns = ["呼号", "状态", "创建时间", "更新时间"]
    df["创建时间"] = (
        pd.to_datetime(df["创建时间"], unit="s") + pd.Timedelta(hours=8)
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    df["更新时间"] = (
        pd.to_datetime(df["更新时间"], unit="s") + pd.Timedelta(hours=8)
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    print(df)
    df.to_excel("QSL.xlsx", index=False)
    conn.close()


if __name__ == "__main__":
    export_to_excel()
