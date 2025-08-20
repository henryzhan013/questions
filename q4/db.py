# q4/db.py
from __future__ import annotations
import os
from datetime import date
from typing import Iterable
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, Float, BigInteger
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from dotenv import load_dotenv

load_dotenv()

def get_engine() -> Engine:
    url = os.getenv("DATABASE_URL", "sqlite:///data/ashare.db")
    if url.startswith("sqlite:///"):
        db_path = url.split("sqlite:///")[-1]
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    return create_engine(url, future=True)

metadata = MetaData()
daily_bars = Table(
    "daily_bars", metadata,
    Column("code",   String(12), primary_key=True),
    Column("date",   Date,       primary_key=True),
    Column("open",   Float),
    Column("high",   Float),
    Column("low",    Float),
    Column("close",  Float),
    Column("volume", BigInteger),
    Column("amount", Float),
)

def ensure_tables(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    req = ["code","date","open","high","low","close","volume","amount"]
    miss = [c for c in req if c not in df.columns]
    if miss:
        raise ValueError(f"missing columns: {miss}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.date
    for c in ["open","high","low","close","volume","amount"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date","open","high","low","close"])
    return out[req]

def _upsert_rows(engine: Engine, rows: Iterable[dict]) -> int:
    stmt = sqlite_insert(daily_bars).values(list(rows))
    update_cols = {c.name: stmt.excluded[c.name] for c in daily_bars.c if c.name not in ("code","date")}
    stmt = stmt.on_conflict_do_update(index_elements=["code","date"], set_=update_cols)
    with engine.begin() as conn:
        res = conn.execute(stmt)
        return res.rowcount or 0

def save_bars(df: pd.DataFrame, chunk: int = 1000, engine: Engine | None = None) -> int:
    engine = engine or get_engine()
    ensure_tables(engine)
    df = _normalize(df)
    total = 0
    for i in range(0, len(df), chunk):
        batch = df.iloc[i:i+chunk]
        total += _upsert_rows(engine, batch.to_dict(orient="records"))
    return total

def max_date_for_code(code: str, engine: Engine | None = None) -> date | None:

    engine = engine or get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            daily_bars.select()
            .with_only_columns(daily_bars.c.date)
            .where(daily_bars.c.code == code)
            .order_by(daily_bars.c.date.desc())
            .limit(1)
        ).first()
    return row[0] if row else None

if __name__ == "__main__":
    from .fetch import fetch_last_year_one
    df = fetch_last_year_one("000001")
    n = save_bars(df)
    print(f"upserted {n} rows into {os.getenv('DATABASE_URL', 'sqlite:///data/ashare.db')}")
