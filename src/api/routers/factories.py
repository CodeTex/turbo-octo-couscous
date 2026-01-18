from robyn import SubRouter

from core.schemas.factory import FactoryCreate, FactoryResponse
from core.services import factory_svc
from core.db.engine import AsyncSessionLocal

factories_router = SubRouter(__name__, prefix="/api/factories")


@factories_router.get("/")
async def list_factories(request):
    async with AsyncSessionLocal() as session:
        factories = await factory_svc.list_factories(session)
        return [FactoryResponse.model_validate(f).model_dump() for f in factories]


@factories_router.get("/:factory_id")
async def get_factory(request):
    factory_id = int(request.path_params["factory_id"])

    async with AsyncSessionLocal() as session:
        factory = await factory_svc.get_factory_by_id(session, factory_id)
        if not factory:
            return {"error": "Factory not found"}
        return FactoryResponse.model_validate(factory).model_dump()


@factories_router.post("/")
async def create_factory(request):
    body = request.body
    factory_data = FactoryCreate(**body)

    async with AsyncSessionLocal() as session:
        factory = await factory_svc.create_factory(session, factory_data)
        return FactoryResponse.model_validate(factory).model_dump()


@factories_router.delete("/:factory_id")
async def delete_factory(request):
    factory_id = int(request.path_params["factory_id"])

    async with AsyncSessionLocal() as session:
        deleted = await factory_svc.delete_factory(session, factory_id)
        if not deleted:
            return {"error": "Factory not found"}
        return {"message": "Factory deleted", "id": factory_id}
