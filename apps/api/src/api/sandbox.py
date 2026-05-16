import ast
import asyncio
import os
import sys
import tempfile

import asyncpg

PREAMBLE = """\
import os, sys, json
import pandas as pd
import numpy as np
import asyncpg
import asyncio
from datetime import date, datetime

_DSN = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:5432/{os.environ['POSTGRES_DB']}"
)


def _to_date(d):
    return date.fromisoformat(d) if isinstance(d, str) else d


async def _q(sql: str, *args) -> list[dict]:
    conn = await asyncpg.connect(_DSN)
    try:
        return [dict(r) for r in await conn.fetch(sql, *args)]
    finally:
        await conn.close()


def get_bars(start_date: str, end_date: str) -> pd.DataFrame:
    return pd.DataFrame(asyncio.run(_q(
        "SELECT * FROM bars WHERE date BETWEEN $1 AND $2 ORDER BY permno, date",
        _to_date(start_date), _to_date(end_date),
    )))


def get_universe(start_date: str, end_date: str) -> pd.DataFrame:
    return pd.DataFrame(asyncio.run(_q('''
        SELECT b.permno, b.date, b.open, b.high, b.low, b.close, b.vol,
               b.daily_return, b.daily_return_wo_distribution, b.market_cap,
               h.ticker, h.issuer_name, h.sic_code
        FROM bars b
        JOIN header h USING (permno)
        WHERE b.date BETWEEN $1 AND $2
          AND b.close IS NOT NULL
        ORDER BY b.permno, b.date
    ''', _to_date(start_date), _to_date(end_date))))


def get_fundamentals(start_date: str, end_date: str) -> pd.DataFrame:
    return pd.DataFrame(asyncio.run(_q('''
        SELECT f.*, l.permno
        FROM fundamentals_quarterly f
        JOIN link l USING (gvkey)
        WHERE f.datadate BETWEEN $1 AND $2
          AND l.link_start_date <= f.datadate
          AND (l.link_end_date IS NULL OR l.link_end_date >= f.datadate)
          AND l.link_primary IN ('P', 'C')
          AND f.indfmt = 'INDL' AND f.datafmt = 'STD'
          AND f.consol = 'C' AND f.popsrc = 'D'
        ORDER BY f.gvkey, f.datadate
    ''', _to_date(start_date), _to_date(end_date))))


def query(sql: str, *args) -> pd.DataFrame:
    return pd.DataFrame(asyncio.run(_q(sql, *args)))


def compute_metrics(returns: pd.Series, initial_capital: float = 1_000_000.0, freq: str = "D") -> dict:
    # freq: 'D' daily (default), 'M' monthly, 'W' weekly
    periods_per_year = {"D": 252, "M": 12, "W": 52}.get(freq, 252)
    returns = returns.dropna()
    if len(returns) == 0:
        return {}
    cum = (1 + returns).cumprod()
    total_ret = float(cum.iloc[-1] - 1)
    n_years = len(returns) / periods_per_year
    ann_ret = float((1 + total_ret) ** (1 / n_years) - 1) if n_years > 0 else 0.0
    ann_vol = float(returns.std() * np.sqrt(periods_per_year))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    max_dd = float((cum / cum.cummax() - 1).min())
    calmar = ann_ret / abs(max_dd) if max_dd < 0 else float("inf")
    return {
        "total_return": round(total_ret, 6),
        "annualized_return": round(ann_ret, 6),
        "annualized_volatility": round(ann_vol, 6),
        "sharpe_ratio": round(sharpe, 6),
        "max_drawdown": round(max_dd, 6),
        "calmar_ratio": round(calmar, 6),
        "n_periods": len(returns),
        "n_years": round(n_years, 2),
    }
"""


_BLOCKED_MODULES = {"subprocess", "socket", "requests", "httpx", "urllib", "ftplib", "smtplib", "paramiko"}
_BLOCKED_ATTRS = {"system", "popen", "rmtree"}


def preflight(code: str) -> str | None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _BLOCKED_MODULES:
                    return f"Blocked import: {alias.name}"
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _BLOCKED_MODULES:
                return f"Blocked import: {node.module}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _BLOCKED_ATTRS:
                return f"Blocked call: .{node.func.attr}()"

    return None


_dsn: str = ""
_schema_cache: str = ""


def _build_dsn() -> str:
    return (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:5432/{os.environ['POSTGRES_DB']}"
    )


async def fetch_schema() -> str:
    global _schema_cache
    if _schema_cache:
        return _schema_cache

    conn = await asyncpg.connect(_build_dsn())
    try:
        rows = await conn.fetch("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('bars', 'header', 'fundamentals_quarterly', 'link', 'adjustment')
            ORDER BY table_name, ordinal_position
        """)
    finally:
        await conn.close()

    tables: dict[str, list[str]] = {}
    for row in rows:
        tables.setdefault(row["table_name"], []).append(
            f"{row['column_name']} ({row['data_type']})"
        )

    _schema_cache = "\n".join(
        f"**{tbl}**: {', '.join(cols)}" for tbl, cols in sorted(tables.items())
    )
    return _schema_cache


async def execute_code(code: str, timeout: int = 120) -> dict:
    if err := preflight(code):
        return {"stdout": "", "stderr": err, "returncode": 1}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(PREAMBLE + "\n\n" + code)
        tmp = f.name
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, tmp,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {"stdout": "", "stderr": f"Timed out after {timeout}s.", "returncode": -1}
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "returncode": proc.returncode,
        }
    finally:
        os.unlink(tmp)
