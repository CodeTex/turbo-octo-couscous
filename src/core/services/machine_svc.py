from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Machine
from core.schemas.machine import MachineCreate


async def list_machines(session: AsyncSession, factory_id: int | None = None) -> list[Machine]:
    query = select(Machine)
    if factory_id:
        query = query.where(Machine.factory_id == factory_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_machine_by_id(session: AsyncSession, machine_id: int) -> Machine | None:
    result = await session.execute(select(Machine).where(Machine.id == machine_id))
    return result.scalar_one_or_none()


async def create_machine(session: AsyncSession, machine_data: MachineCreate) -> Machine:
    machine = Machine(**machine_data.model_dump())
    session.add(machine)
    await session.commit()
    await session.refresh(machine)
    return machine


async def delete_machine(session: AsyncSession, machine_id: int) -> bool:
    machine = await get_machine_by_id(session, machine_id)
    if not machine:
        return False
    await session.delete(machine)
    await session.commit()
    return True
