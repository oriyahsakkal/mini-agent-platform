from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.deps import get_tenant_id, get_db
from app.db.models import Tool
from app.schemas import ToolCreate, ToolUpdate, ToolOut

router = APIRouter(tags=["tools"])


@router.post("/tools", response_model=ToolOut, status_code=201)
def create_tool(
    payload: ToolCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tool = Tool(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
    )

    db.add(tool)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409,
            detail="Tool name already exists for this tenant",
        )
    except Exception:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(tool)
    return tool


@router.get("/tools", response_model=list[ToolOut])
def list_tools(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tools = (
        db.query(Tool).filter(Tool.tenant_id == tenant_id).order_by(Tool.id.asc()).all()
    )
    return tools


@router.get("/tools/{tool_id}", response_model=ToolOut)
def get_tool(
    tool_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tool = (
        db.query(Tool)
        .filter(
            Tool.id == tool_id,
            Tool.tenant_id == tenant_id,
        )
        .first()
    )

    if not tool:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Tool not found")

    return tool


@router.put("/tools/{tool_id}", response_model=ToolOut)
def update_tool(
    tool_id: int,
    payload: ToolUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tool = (
        db.query(Tool)
        .filter(
            Tool.id == tool_id,
            Tool.tenant_id == tenant_id,
        )
        .first()
    )

    if not tool:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Tool not found")

    if payload.name is not None:
        tool.name = payload.name
    if payload.description is not None:
        tool.description = payload.description

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409, detail="Tool name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(tool)
    return tool


@router.delete("/tools/{tool_id}", status_code=204)
def delete_tool(
    tool_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tool = (
        db.query(Tool)
        .filter(
            Tool.id == tool_id,
            Tool.tenant_id == tenant_id,
        )
        .first()
    )

    if not tool:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Tool not found")

    db.delete(tool)
    db.commit()
    return None
