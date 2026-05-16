from common.db import dsn
import asyncpg
import yaml
from pathlib import Path
import asyncio

with open(Path(__file__).parent / "universe.yml", mode="r") as f:
    config = yaml.safe_load(f)

UNIVERSE = config["universe"]
PARAMS = config["params"]

async def get_permno_list():
    QUERY = """
    SELECT permno FROM header WHERE
    ticker = ANY($1);
    """
    conn = await asyncpg.connect(dsn)
    try:
        result = await conn.fetch(QUERY, UNIVERSE)
    finally:
        await conn.close()
    return [record["permno"] for record in result]

async def get_permno_string():
    return ",".join([str(permno) for permno in await get_permno_list()])

async def get_params(starting_offset: int):
    base_params = PARAMS.copy()
    base_params["offset"] = starting_offset
    if UNIVERSE is None:
        return base_params
    permno_string = await get_permno_string()
    base_params["permno__in"] = permno_string
    return base_params
