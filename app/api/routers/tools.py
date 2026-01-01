from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.error_map import raise_http
from app.deps import get_tenant_id, get_db
from app.schemas import ToolCreate, ToolUpdate, ToolOut
from app.repositories.tools_repo import ToolsRepository
from app.services.tools_service import ToolsService

router = APIRouter(tags=["tools"])


@router.post("/tools", response_model=ToolOut, status_code=201)
def create_tool(
    payload: ToolCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    try:
        service = ToolsService(ToolsRepository(db))
        return service.create(tenant_id, payload.name, payload.description)
    except Exception as e:
        raise_http(e)


@router.get("/tools", response_model=list[ToolOut])
def list_tools(tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)):
    service = ToolsService(ToolsRepository(db))
    return service.list(tenant_id)


@router.get("/tools/{tool_id}", response_model=ToolOut)
def get_tool(
    tool_id: int, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)
):
    try:
        service = ToolsService(ToolsRepository(db))
        return service.get(tenant_id, tool_id)
    except Exception as e:
        raise_http(e)


@router.put("/tools/{tool_id}", response_model=ToolOut)
def update_tool(
    tool_id: int,
    payload: ToolUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    try:
        service = ToolsService(ToolsRepository(db))
        return service.update(tenant_id, tool_id, payload.name, payload.description)
    except Exception as e:
        raise_http(e)


@router.delete("/tools/{tool_id}", status_code=204)
def delete_tool(
    tool_id: int, tenant_id: str = Depends(get_tenant_id), db: Session = Depends(get_db)
):
    try:
        service = ToolsService(ToolsRepository(db))
        service.delete(tenant_id, tool_id)
        return None
    except Exception as e:
        raise_http(e)
