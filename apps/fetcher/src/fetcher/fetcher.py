import asyncpg
import httpx
import os
from common.logger import get_logger
from common import mapping
import asyncio
import argparse
from common.db import dsn

logger = get_logger(__name__)
parser = argparse.ArgumentParser(
    prog="fetcher script",
    description="fetches from wrds and inserts into a given table",
)

parser.add_argument("-h", "--headers",action='store_true')

class WRDSFetcher:
    def __init__(self, connection):
        self.auth = {'Authorization': f'Token {os.environ["WRDS_TOKEN"]}'}
        self.conn = connection
        self.url_root = "https://wrds-api.wharton.upenn.edu"

    async def populate_header(self):
        cur_url = self.url_root + "/data/crsp.stksecurityinfohdr/"
        while True:
            logger.info("CURRENT URL: %s", cur_url)
            try:
                async with httpx.AsyncClient as client:
                    response = await client.get(cur_url, headers=self.auth)
                    response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("STATUS CODE: %s", str(response.status_code))
                await asyncio.sleep(10)
                continue

            result = response.json()
            map = mapping.get_mapping("header")
            insert_cols = mapping.get_insert_cols(map)
            placeholders = mapping.get_placeholders(map)
            insert_tups = mapping.get_tuples(result["results"], map)

            QUERY = f"""
            INSERT INTO headers ({insert_cols})
                VALUES ({placeholders});
            """

            await self.conn.executemany(
                QUERY,
                insert_tups
            )

            if result["next"] is None:
                logger.info("HEADER FETCHING COMPLETE")
                break
            else:
                cur_url = result["next"]

async def fetch():
    args = parser.parse_args()
    try:
        conn = await asyncpg.connect(dsn)
        fetcher = WRDSFetcher(conn)
        if args.headers:
            logger.info("RUNNING HEADER FETCH")
            await fetcher.populate_header()

    finally:
        conn.close()


def main():
    asyncio.run(fetch())

if __name__ == "__main__":
    main()