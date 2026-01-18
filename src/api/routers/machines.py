from robyn import SubRouter

from core.schemas.machine import MachineCreate, MachineResponse
from core.services import machine_svc
from core.db.engine import AsyncSessionLocal

machines_router = SubRouter(__name__, prefix="/api/machines")


@machines_router.get("/")
async def list_machines(request):
    factory_id = request.query_params.get("factory_id", None)
    factory_id = int(factory_id) if factory_id else None

    async with AsyncSessionLocal() as session:
        machines = await machine_svc.list_machines(session, factory_id)
        return [MachineResponse.model_validate(m).model_dump() for m in machines]


@machines_router.get("/:machine_id")
async def get_machine(request):
    machine_id = int(request.path_params["machine_id"])

    async with AsyncSessionLocal() as session:
        machine = await machine_svc.get_machine_by_id(session, machine_id)
        if not machine:
            return {"error": "Machine not found"}
        return MachineResponse.model_validate(machine).model_dump()


@machines_router.post("/")
async def create_machine(request):
    body = request.body
    machine_data = MachineCreate(**body)

    async with AsyncSessionLocal() as session:
        machine = await machine_svc.create_machine(session, machine_data)
        return MachineResponse.model_validate(machine).model_dump()


@machines_router.delete("/:machine_id")
async def delete_machine(request):
    machine_id = int(request.path_params["machine_id"])

    async with AsyncSessionLocal() as session:
        deleted = await machine_svc.delete_machine(session, machine_id)
        if not deleted:
            return {"error": "Machine not found"}
        return {"message": "Machine deleted", "id": machine_id}
