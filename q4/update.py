# q4/update.py
from __future__ import annotations
import argparse
import datetime as dt
import time
from typing import Iterable, Optional

import pandas as pd

from .fetch import list_a_codes, fetch_hist_one, fetch_last_year_one
from .db import save_bars, max_date_for_code

DATEFMT = "%Y%m%d"

def _ymd(d: dt.date) -> str:
    return d.strftime(DATEFMT)

def update_codes(
    codes: Iterable[str],
    end: Optional[dt.date] = None,
    adjust: Optional[str] = "qfq",
    sleep_sec: float = 0.2,
) -> int:
    if end is None:
        end = dt.date.today()

    total_rows = 0
    for idx, code in enumerate(codes, 1):
        try:
            last = max_date_for_code(code)
            if last is None:
                df = fetch_last_year_one(code, end=end, adjust=adjust)
            else:
                start = last + dt.timedelta(days=1)
                if start > end:
                    continue
                df = fetch_hist_one(code, _ymd(start), _ymd(end), adjust=adjust)

            if not df.empty:
                n = save_bars(df)
                total_rows += n

            if sleep_sec > 0:
                time.sleep(sleep_sec)

        except Exception as e:
            print(f"[WARN] {code}: {e!r}")
            continue

    return total_rows

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Incremental daily update for A-share bars")
    p.add_argument("--end", type=str, default=None, help="YYYYMMDD；默认今天")
    p.add_argument("--codes", type=str, default=None,
                   help="逗号分隔的代码列表，如 000001,600519；默认全市场")
    p.add_argument("--limit", type=int, default=None, help="只处理前 N 只代码用于测试")
    p.add_argument("--sleep", type=float, default=0.2, help="每只股票之间的休眠秒数")
    p.add_argument("--adjust", type=str, default="qfq", help="复权方式：qfq/hfq/None")
    return p.parse_args()

def main():
    args = parse_args()
    end = dt.datetime.strptime(args.end, DATEFMT).date() if args.end else None

    if args.codes:
        codes = [c.strip().zfill(6) for c in args.codes.split(",") if c.strip()]
    else:
        codes = list_a_codes()

    if args.limit:
        codes = codes[:args.limit]

    print(f"[INFO] updating {len(codes)} codes, end={end or dt.date.today()}, adjust={args.adjust}")
    rows = update_codes(codes, end=end, adjust=args.adjust, sleep_sec=args.sleep)
    print(f"[DONE] upserted {rows} rows in total.")

if __name__ == "__main__":
    main()
