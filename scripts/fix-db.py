"""One-time fix: create placement_focusbar if missing and verify init."""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
import asyncpg

load_dotenv()


async def main():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("ERROR: DATABASE_URL not set in .env")
        return 1

    part = url.replace("postgresql+asyncpg://", "")
    creds, rest = part.split("@")
    user, password = creds.split(":", 1)
    hostport, _db = rest.split("/", 1)
    host, port = hostport.split(":")

    conn = await asyncpg.connect(
        user=user, password=password, host=host, port=int(port), database="postgres"
    )
    rows = await conn.fetch(
        "SELECT datname FROM pg_database WHERE datname = 'placement_focusbar'"
    )
    if not rows:
        await conn.execute("CREATE DATABASE placement_focusbar")
        print("Created placement_focusbar")
    else:
        print("Database already exists")
    await conn.close()

    from backend.db.init_db import init_db

    ok = await init_db()
    print("DB init:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
