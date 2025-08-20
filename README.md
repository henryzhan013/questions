# 数据抓取与增量更新（branch `2`）

使用 `akshare` 抓取 A 股日线数据，落库到 SQLite，支持每日增量与数据校验/修复。

## 准备
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

# 配置数据库（可选，默认 sqlite:///data/ashare.db）
```bash
mkdir -p data
echo "DATABASE_URL=sqlite:///data/ashare.db" > .env
```


### `q4/fetch.py`（拉数据）
- **作用**：用 `akshare` 获取 A 股日线，标准化为统一列。
- **主要函数**：
  - `list_a_codes() -> list[str]`：返回全部 A 股代码（六位字符串）。
  - `fetch_hist_one(symbol, start, end, adjust='qfq') -> DataFrame`  
    输入日期格式 `YYYYMMDD`；输出列：`['code','date','open','high','low','close','volume','amount']`，`date` 为 `YYYY-MM-DD`。
  - `fetch_last_year_one(symbol, end=None, adjust='qfq') -> DataFrame`：抓单票近一年。
- **备注**：内部适配了 akshare 不同版本的中英文字段名，省心。

### `q4/db.py`（建表与落库）
- **作用**：管理数据库连接与表结构，提供**幂等 upsert** 写入。
- **读取**：`.env` 的 `DATABASE_URL`（默认 `sqlite:///data/ashare.db`）。
- **表结构**：`daily_bars(code, date, open, high, low, close, volume, amount)`，主键 `(code, date)`。
- **主要函数**：
  - `get_engine() -> Engine`：创建连接（会自动创建 `data/` 目录）。
  - `ensure_tables(engine=None)`：建表（按需）。
  - `save_bars(df, chunk=1000, engine=None) -> int`：批量 upsert，返回受影响行数。
  - `max_date_for_code(code, engine=None) -> date | None`：查询某票最新日期。

### `q4/update.py`（每日增量）
- **作用**：按代码列表做**增量更新**；库里有最新日就从+1天拉到指定 `end`，没有就补近一年。
- **核心函数**：  
  - `update_codes(codes, end=None, adjust='qfq', sleep_sec=0.2) -> int`：返回总写入行数。
- **命令行用法**：  
  - `--codes 000001,600519` 指定代码  
  - `--limit 50` 只跑前 N 只（调试用）  
  - `--end YYYYMMDD` 指定截止日  
  - `--sleep 0.2` 限速，别把数据源打懵  
  - `--adjust qfq|hfq|None` 复权方式

### `q4/validate.py`（校验与修复）
- **作用**：检查某天是否完整；只补缺失；或全量重灌近一年；也能扫最近 N 天做体检。
- **子命令**：
  - `check-day --date YYYY-MM-DD`：打印当日现有数量、期望数量、缺失样本。
  - `repair-day --date YYYY-MM-DD [--limit N] [--sleep 0.2]`：只为缺失代码补当日。
  - `rehydrate [--limit N] [--end YYYY-MM-DD]`：全市场近一年重灌（库空或冷启动时用）。
  - `scan --days 5`：扫描最近 N 天的完整性。
- **小提示**：停牌/新股导致的“自然缺失”很正常，`check-day` 是体检，不是宣判。


