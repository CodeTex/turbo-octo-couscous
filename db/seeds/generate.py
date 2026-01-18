import asyncio
from pathlib import Path

import aiosqlite


async def seed_data():
    db_path = Path("data/factory.db")

    if not db_path.exists():
        print("Error: Database not found. Run 'just migrate' first.")
        return

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("DELETE FROM factories")
        await conn.commit()

        factories = [
            ("Factory Alpha", "Berlin, Germany"),
            ("Factory Beta", "Tokyo, Japan"),
            ("Factory Gamma", "San Francisco, USA"),
            ("Factory Delta", "Mumbai, India"),
            ("Factory Epsilon", "São Paulo, Brazil"),
        ]

        await conn.executemany("INSERT INTO factories (name, location) VALUES (?, ?)", factories)
        await conn.commit()

        print(f"✓ Seeded {len(factories)} factories")


if __name__ == "__main__":
    asyncio.run(seed_data())
