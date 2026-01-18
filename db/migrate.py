import asyncio
import os
from pathlib import Path

import aiosqlite


async def run_migrations():
    migrations_dir = Path(__file__).parent / "migrations"
    db_path = Path("data/factory.db")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")

        migration_files = sorted(migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            print(f"Running migration: {migration_file.name}")
            sql = migration_file.read_text()
            await conn.executescript(sql)
            await conn.commit()

        print(f"✓ Applied {len(migration_files)} migration(s)")


if __name__ == "__main__":
    asyncio.run(run_migrations())
