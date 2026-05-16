import asyncpg
import asyncio
from common.db import PROJECT_ROOT, dsn
import argparse

parser = argparse.ArgumentParser(
    prog="db setup script",
    description="runs one-time setup operations",
)

parser.add_argument("--ddl", action='store_true')
parser.add_argument("--views", action='store_true')
args = parser.parse_args()

async def execute_ddl():
    if args.ddl:
        sql_script = "DDL.sql"
    elif args.views:
        sql_script = "views.sql"
    else:
        raise ValueError("one of ddl or views must be set")
    conn = await asyncpg.connect(dsn)
    try:
        with open(PROJECT_ROOT / "apps" / "setup" / sql_script, mode="r") as ddl_command:
            await conn.execute(ddl_command.read())

    finally:
        await conn.close()

def main():
    asyncio.run(execute_ddl())

if __name__ == "__main__":
    main()
