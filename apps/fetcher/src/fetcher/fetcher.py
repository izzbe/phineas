import asyncpg
import httpx
import os
from common.logger import get_logger
from common import mapping
import asyncio
import argparse
from common.db import dsn
from common.universe import get_params

logger = get_logger(__name__)
parser = argparse.ArgumentParser(
    prog="fetcher script",
    description="fetches from wrds and inserts into a given table",
)

parser.add_argument( "--headers", action='store_true')
parser.add_argument( "--bars", action='store_true')
parser.add_argument( "--fundamentals_quarterly", action='store_true')
parser.add_argument( "--link", action='store_true')
parser.add_argument( "--adjustment", action='store_true')
parser.add_argument("--offset", type=int, default=0)
parser.add_argument("--limit", type=int, default=0)

class WRDSFetcher:
    def __init__(self, connection):
        self.auth = {'Authorization': f'Token {os.environ["WRDS_TOKEN"]}'}
        self.conn = connection
        self.url_root = "https://wrds-api.wharton.upenn.edu"

    async def fetch(self, params, schema_name: str):
        cur_url = self.url_root + mapping.get_url(schema_name)
        while True:
            logger.info("CURRENT PARAMS: %s", params)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(cur_url, headers=self.auth, timeout=360, params=params)
                    response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("STATUS CODE: %s", str(response.status_code))
                await asyncio.sleep(10)
                continue

            result = response.json()

            logger.info("GET REQUEST SUCCESFUL. %d TOTAL ROW COUNT", result["count"])

            map = mapping.get_mapping(schema_name)
            insert_cols = mapping.get_insert_cols(map)
            placeholders = mapping.get_placeholders(map)
            insert_tups = mapping.get_tuples(result["results"], schema_name, map)

            QUERY = f"""
            INSERT INTO {schema_name} ({insert_cols})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING;
            """

            logger.info("INSERTING %d ROWS", len(result["results"]))
            await self.conn.executemany(
                QUERY,
                insert_tups
            )

            if result["next"] is None:
                logger.info("%s FETCHING COMPLETE", schema_name)
                break
            else:
                if "offset" not in params:
                    params["offset"] = 0
                params["offset"] += params["limit"]

async def fetch():
    args = parser.parse_args()
    params = await get_params(args.offset)
    if args.limit:
        params["limit"] = args.limit
    try:
        conn = await asyncpg.connect(dsn)
        fetcher = WRDSFetcher(conn)
        if args.headers:
            logger.info("RUNNING HEADER FETCH")
            await fetcher.fetch(params, "header")
        if args.bars:
            logger.info("RUNNING BAR FETCH")
            await fetcher.fetch(params, "bars")
        if args.fundamentals_quarterly:
            logger.info("RUNNING FUNDAMENTAL QUARTERLY FETCH")
            await fetcher.fetch(params, "fundamentals_quarterly")
        if args.link:
            logger.info("RUNNING link FETCH")
            await fetcher.fetch(params, "link")
        if args.adjustment:
            logger.info("RUNNING adjustment FETCH")
            await fetcher.fetch(params, "adjustment")
    finally:
        await conn.close()


def main():
    asyncio.run(fetch())

if __name__ == "__main__":
    main()