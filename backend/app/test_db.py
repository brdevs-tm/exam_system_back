import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def main():
    dsn = os.getenv("ASYNC_PG_DSN")
    print("ASYNC_PG_DSN =", dsn)

    conn = await asyncpg.connect(dsn)
    val = await conn.fetchval("SELECT 1;")
    print("SELECT 1 =>", val)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
