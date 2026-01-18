import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import random

import aiosqlite


async def seed_data():
    db_path = Path("data/factory.db")

    if not db_path.exists():
        print("Error: Database not found. Run 'just migrate' first.")
        return

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("DELETE FROM readings")
        await conn.execute("DELETE FROM sensors")
        await conn.execute("DELETE FROM machines")
        await conn.execute("DELETE FROM factories")
        await conn.execute("DELETE FROM sqlite_sequence")
        await conn.commit()

        factories = [
            ("Factory Alpha", "Berlin, Germany"),
            ("Factory Beta", "Tokyo, Japan"),
            ("Factory Gamma", "San Francisco, USA"),
            ("Factory Delta", "Mumbai, India"),
            ("Factory Epsilon", "São Paulo, Brazil"),
        ]

        cursor = await conn.executemany(
            "INSERT INTO factories (name, location) VALUES (?, ?)", factories
        )
        await conn.commit()

        machines = [
            (1, "CNC Mill 001", "CNC_MILL", "OPERATIONAL"),
            (1, "Laser Cutter 001", "LASER_CUTTER", "OPERATIONAL"),
            (1, "Robot Arm 001", "ROBOT_ARM", "MAINTENANCE"),
            (2, "CNC Mill 002", "CNC_MILL", "OPERATIONAL"),
            (2, "3D Printer 001", "3D_PRINTER", "OPERATIONAL"),
            (3, "Assembly Line 001", "ASSEMBLY_LINE", "OPERATIONAL"),
            (3, "Robot Arm 002", "ROBOT_ARM", "OPERATIONAL"),
            (4, "Injection Molder 001", "INJECTION_MOLDER", "OPERATIONAL"),
            (5, "CNC Mill 003", "CNC_MILL", "OFFLINE"),
        ]

        await conn.executemany(
            "INSERT INTO machines (factory_id, name, type, status) VALUES (?, ?, ?, ?)", machines
        )
        await conn.commit()

        sensors = [
            (1, "Temperature Sensor", "celsius", 15.0, 85.0),
            (1, "Vibration Sensor", "hz", 0.0, 100.0),
            (2, "Power Sensor", "watts", 100.0, 5000.0),
            (3, "Pressure Sensor", "psi", 20.0, 150.0),
            (4, "Temperature Sensor", "celsius", 15.0, 85.0),
            (4, "Speed Sensor", "rpm", 0.0, 3000.0),
            (5, "Temperature Sensor", "celsius", 15.0, 85.0),
            (6, "Speed Sensor", "meters_per_min", 0.0, 100.0),
            (6, "Quality Sensor", "percent", 90.0, 100.0),
            (7, "Position Sensor", "mm", None, None),
            (7, "Force Sensor", "newtons", 0.0, 1000.0),
            (8, "Temperature Sensor", "celsius", 180.0, 250.0),
            (8, "Pressure Sensor", "bar", 50.0, 200.0),
            (9, "Temperature Sensor", "celsius", 15.0, 85.0),
        ]

        await conn.executemany(
            "INSERT INTO sensors (machine_id, name, unit, min_threshold, max_threshold) VALUES (?, ?, ?, ?, ?)",
            sensors,
        )
        await conn.commit()

        readings = []
        now = datetime.utcnow()
        for sensor_id in range(1, len(sensors) + 1):
            sensor = sensors[sensor_id - 1]
            min_val = sensor[3] if sensor[3] is not None else 0
            max_val = sensor[4] if sensor[4] is not None else 100

            for i in range(20):
                timestamp = now - timedelta(hours=20 - i)
                value = random.uniform(min_val, max_val)
                readings.append((sensor_id, value, timestamp.isoformat()))

        await conn.executemany(
            "INSERT INTO readings (sensor_id, value, timestamp) VALUES (?, ?, ?)",
            readings,
        )
        await conn.commit()

        print(
            f"✓ Seeded {len(factories)} factories, {len(machines)} machines, {len(sensors)} sensors, and {len(readings)} readings"
        )


if __name__ == "__main__":
    asyncio.run(seed_data())
