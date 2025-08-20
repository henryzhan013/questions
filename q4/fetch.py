# q4_fetch.py
from __future__ import annotations
import datetime as dt
import akshare as ak
import pandas as pd

def list_a_codes() -> list[str]:
    df = ak.stock_info_a_code_name()
    for col in ["code", "证券代码", "股票代码"]:
        if col in df.columns:
            codes = df[col].astype(str).str.zfill(6).tolist()
            return codes
    raise RuntimeError(f"Unexpected columns: {df.columns.tolist()}")

def fetch_hist_one(symbol: str, start: str, end: str, adjust: str | None = "qfq") -> pd.DataFrame:
    df = ak.stock_zh_a_hist(
        symbol=symbol, period="daily",
        start_date=start, end_date=end, adjust=adjust
    )
    rename_map = {
        "日期": "date", "开盘": "open", "最高": "high", "最低": "low",
        "收盘": "close", "成交量": "volume", "成交额": "amount",
        "日期Date": "date", "开盘Open": "open", "最高High": "high", "最低Low": "low",
        "收盘Close": "close", "成交量Volume": "volume", "成交额Amount": "amount",
    }
    df = df.rename(columns=rename_map)
    keep = ["date", "open", "high", "low", "close", "volume", "amount"]
    df = df[keep]
    df.insert(0, "code", symbol)
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    return df

def fetch_last_year_one(symbol: str, end: dt.date | None = None, adjust: str | None = "qfq") -> pd.DataFrame:
    if end is None:
        end = dt.date.today()
    start = end - dt.timedelta(days=365)
    return fetch_hist_one(symbol, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), adjust)

if __name__ == "__main__":
    end = dt.date.today()
    start = end - dt.timedelta(days=30)
    df = fetch_hist_one("000001", start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    print(df.head())
    print("rows:", len(df), "cols:", list(df.columns))
