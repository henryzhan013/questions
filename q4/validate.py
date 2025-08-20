# q4/validate.py
from __future__ import annotations
import argparse
import datetime as dt
import time
from typing import Iterable, Optional, Tuple, Set, List

from sqlalchemy import select, func, distinct
from sqlalchemy.engine import Engine

from .fetch import list_a_codes, fetch_hist_one, fetch_last_year_one
from .db import get_engine, ensure_tables, daily_bars, save_bars

DATEFMT = "%Y-%m-%d"


def _parse_date(s: str) -> dt.date:
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return dt.datetime.strptime(s, "%Y%m%d").date()
    return dt.datetime.strptime(s, "%Y-%m-%d").date()

def _ymd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")

def _table_rowcount(engine: Engine) -> int:
    with engine.begin() as conn:
        return conn.execute(select(func.count()).select_from(daily_bars)).scalar_one()

def present_codes_on(engine: Engine, day: dt.date) -> Set[str]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(distinct(daily_bars.c.code)).where(daily_bars.c.date == day)
        ).scalars().all()
    return set(rows)

def dates_span(engine: Engine) -> Tuple[Optional[dt.date], Optional[dt.date]]:
    with engine.begin() as conn:
        row = conn.execute(
            select(func.min(daily_bars.c.date), func.max(daily_bars.c.date))
        ).first()
    return (row[0], row[1]) if row else (None, None)


def cmd_check_day(day: dt.date, expect: Optional[Iterable[str]] = None) -> Tuple[int, List[str]]:
    engine = get_engine()
    ensure_tables(engine)

    have = present_codes_on(engine, day)
    if expect is None:
        expect = list_a_codes()
    expect_set = {c.strip().zfill(6) for c in expect}
    missing = sorted(expect_set - have)
    print(f"[CHECK] {day} present={len(have)} expected={len(expect_set)} missing={len(missing)}")
    if missing:
        print("missing sample:", ", ".join(missing[:20]), "..." if len(missing) > 20 else "")
    return len(missing), missing

def cmd_repair_day(day: dt.date, missing: Optional[Iterable[str]] = None,
                   adjust: Optional[str] = "qfq", sleep: float = 0.2, limit: Optional[int] = None) -> int:
    engine = get_engine()
    ensure_tables(engine)

    if missing is None:
        _, missing = cmd_check_day(day)
    codes = [c.strip().zfill(6) for c in missing]
    if limit:
        codes = codes[:limit]

    total = 0
    for i, code in enumerate(codes, 1):
        try:
            df = fetch_hist_one(code, _ymd(day), _ymd(day), adjust=adjust)
            if not df.empty:
                total += save_bars(df, engine=engine)
            if sleep > 0:
                time.sleep(sleep)
        except Exception as e:
            print(f"[WARN] repair {code} @ {day}: {e!r}")
    print(f"[REPAIR] {day} upserted={total} rows for {len(codes)} codes")
    return total

def cmd_rehydrate(end: Optional[dt.date] = None, adjust: Optional[str] = "qfq",
                  limit: Optional[int] = None, sleep: float = 0.2) -> int:
    engine = get_engine()
    ensure_tables(engine)

    codes = list_a_codes()
    if limit:
        codes = codes[:limit]

    total = 0
    for i, code in enumerate(codes, 1):
        try:
            df = fetch_last_year_one(code, end=end, adjust=adjust)
            if not df.empty:
                total += save_bars(df, engine=engine)
            if sleep > 0:
                time.sleep(sleep)
        except Exception as e:
            print(f"[WARN] rehydrate {code}: {e!r}")
    print(f"[REHYDRATE] upserted={total} rows for {len(codes)} codes")
    return total

def cmd_scan(days: int = 5) -> None:

    engine = get_engine()
    ensure_tables(engine)

    today = dt.date.today()
    expect = list_a_codes()
    for d in (today - dt.timedelta(days=i) for i in range(days)):
        miss_cnt, _ = cmd_check_day(d, expect=expect)
        span_min, span_max = dates_span(engine)
        print(f"[SPAN] in DB: {span_min} .. {span_max}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate and repair A-share daily bars")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("check-day", help="检查某一天的完整性")
    p1.add_argument("--date", required=True, help="YYYY-MM-DD 或 YYYYMMDD")

    p2 = sub.add_parser("repair-day", help="为缺失代码补齐某一天的数据")
    p2.add_argument("--date", required=True, help="YYYY-MM-DD 或 YYYYMMDD")
    p2.add_argument("--adjust", default="qfq", help="qfq/hfq/None")
    p2.add_argument("--sleep", type=float, default=0.2)
    p2.add_argument("--limit", type=int, default=None)

    p3 = sub.add_parser("rehydrate", help="全量恢复：近一年全市场")
    p3.add_argument("--end", default=None, help="结束日 YYYY-MM-DD/YYMMDD，默认今天")
    p3.add_argument("--adjust", default="qfq")
    p3.add_argument("--sleep", type=float, default=0.2)
    p3.add_argument("--limit", type=int, default=None)

    p4 = sub.add_parser("scan", help="扫描最近 N 天完整性")
    p4.add_argument("--days", type=int, default=5)

    return p.parse_args()

def main():
    args = parse_args()
    if args.cmd == "check-day":
        day = _parse_date(args.date)
        cmd_check_day(day)
    elif args.cmd == "repair-day":
        day = _parse_date(args.date)
        cmd_repair_day(day, adjust=args.adjust, sleep=args.sleep, limit=args.limit)
    elif args.cmd == "rehydrate":
        end = _parse_date(args.end) if args.end else None
        cmd_rehydrate(end=end, adjust=args.adjust, limit=args.limit, sleep=args.sleep)
    elif args.cmd == "scan":
        cmd_scan(days=args.days)
    else:
        raise SystemExit("unknown command")

if __name__ == "__main__":
    main()
