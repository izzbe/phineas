import os
from typing import AsyncIterator

import anthropic

from .sandbox import execute_code, fetch_schema
from .schemas import BacktestRequest

_SYSTEM_PROMPT_TEMPLATE = """You are Phineas, a quantitative finance AI that implements algorithmic trading backtests.

## Database schema (PostgreSQL + TimescaleDB)

{schema}

**Key notes:**
- bars.daily_return includes distributions; daily_return_wo_distribution is price-only
- fundamentals_quarterly.rdq is the earnings announcement date — use it (not datadate) for point-in-time signals
- link.link_primary: use 'P' or 'C'; link_type: use 'LC', 'LU', 'LS'

## Sandbox environment

Pre-available (no imports needed):
```python
get_universe(start_date: str, end_date: str) -> pd.DataFrame   # bars + header joined
get_bars(start_date: str, end_date: str) -> pd.DataFrame
get_fundamentals(start_date: str, end_date: str) -> pd.DataFrame  # joined to permno via link
query(sql: str, *args) -> pd.DataFrame
compute_metrics(returns: pd.Series, initial_capital: float = 1_000_000, freq: str = "D") -> dict
# freq: "D" daily (default), "M" monthly, "W" weekly — must match the return series frequency
pd, np, json, asyncio, os
```

## Rules

1. **Each `execute_python` call is a completely fresh Python process — no state carries over between calls.** Always include all data-loading and setup code in the same call that uses it. Never split work across multiple calls expecting variables to persist.
2. No look-ahead bias — only use data available at each rebalance date.
3. For fundamental signals use `rdq` (announcement date), not `datadate`.
4. Prefer a single comprehensive `execute_python` call over many exploratory ones. If iteration is needed (e.g., to fix a bug), repeat all prior setup code in the new call.
5. Final output: `print(json.dumps(results, default=str))` where `results` MUST include:
   - `metrics`: from `compute_metrics()` with correct `freq`
   - `equity_curve`: `{date_str: portfolio_value}` dict for every rebalance period — this is required for charting"""


async def run_backtest(request: BacktestRequest) -> AsyncIterator[dict]:
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    schema = await fetch_schema()
    system = _SYSTEM_PROMPT_TEMPLATE.replace("{schema}", schema)

    tools: list[anthropic.types.ToolParam] = [
        {
            "name": "execute_python",
            "description": "Execute Python in the Phineas backtest sandbox.",
            "input_schema": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        }
    ]

    messages: list[anthropic.types.MessageParam] = [
        {
            "role": "user",
            "content": (
                f"Strategy:\n\n{request.strategy}\n\n"
                f"Parameters: start={request.start_date}, end={request.end_date}, "
                f"capital=${request.initial_capital:,.0f}"
            ),
        }
    ]

    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=system,
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text":
                yield {"type": "thinking", "content": block.text}

        if response.stop_reason == "end_turn":
            yield {"type": "done"}
            break

        if response.stop_reason != "tool_use":
            yield {"type": "agent_error", "content": f"Unexpected stop_reason: {response.stop_reason}"}
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use" or block.name != "execute_python":
                continue

            code = block.input["code"]
            yield {"type": "code", "content": code}
            yield {"type": "executing"}

            result = await execute_code(code)
            yield {
                "type": "code_output",
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "returncode": result["returncode"],
            }

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": (
                    f"STDOUT:\n{result['stdout']}\n"
                    f"STDERR:\n{result['stderr']}\n"
                    f"returncode: {result['returncode']}"
                ),
            })

        messages.append({"role": "user", "content": tool_results})
