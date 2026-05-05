import asyncpg
import asyncio
from common.db import PROJECT_ROOT, dsn

async def execute_ddl():
    conn = await asyncpg.connect(dsn)
    try:
        with open(PROJECT_ROOT / "apps" / "setup" / "DDL.sql", mode="r") as ddl_command:
            await conn.execute(ddl_command.read())

    finally:
        await conn.close()

def main():
    asyncio.run(execute_ddl())

if __name__ == "__main__":
    main()
