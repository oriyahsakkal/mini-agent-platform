from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.deps import get_tenant_id, get_db
from app.db.models import Tool, Agent
from app.schemas import AgentCreate, AgentUpdate, AgentOut

router = APIRouter(tags=["agents"])


@router.post("/agents", response_model=AgentOut, status_code=201)
def create_agent(
    payload: AgentCreate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    agent = Agent(
        tenant_id=tenant_id,
        name=payload.name,
        role=payload.role,
        description=payload.description,
    )

    if payload.tool_ids:
        tools = (
            db.query(Tool)
            .filter(
                Tool.tenant_id == tenant_id,
                Tool.id.in_(payload.tool_ids),
            )
            .all()
        )

        if len(tools) != len(set(payload.tool_ids)):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400, detail="One or more tools not found for this tenant"
            )

        agent.tools = tools

    db.add(agent)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409, detail="Agent name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(agent)

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[tool.id for tool in agent.tools],
    )


@router.get("/agents", response_model=list[AgentOut])
def list_agents(
    tool_name: str | None = None,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    query = db.query(Agent).filter(Agent.tenant_id == tenant_id)

    if tool_name:
        query = (
            query.join(Agent.tools)
            .filter(Tool.tenant_id == tenant_id, Tool.name == tool_name)
            .distinct()
        )

    agents = query.order_by(Agent.id.asc()).all()

    return [
        AgentOut(
            id=a.id,
            name=a.name,
            role=a.role,
            description=a.description,
            tool_ids=[t.id for t in a.tools],
        )
        for a in agents
    ]


@router.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.tenant_id == tenant_id,
        )
        .first()
    )

    if not agent:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[t.id for t in agent.tools],
    )


@router.put("/agents/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: int,
    payload: AgentUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.tenant_id == tenant_id,
        )
        .first()
    )

    if not agent:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Agent not found")

    if payload.name is not None:
        agent.name = payload.name
    if payload.role is not None:
        agent.role = payload.role
    if payload.description is not None:
        agent.description = payload.description

    # tool_ids semantics:
    # - None  => do not change tools
    # - []    => clear tools
    # - [..]  => replace tools with given list
    if payload.tool_ids is not None:
        if payload.tool_ids:
            tools = (
                db.query(Tool)
                .filter(
                    Tool.tenant_id == tenant_id,
                    Tool.id.in_(payload.tool_ids),
                )
                .all()
            )
            if len(tools) != len(set(payload.tool_ids)):
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail="One or more tools not found for this tenant",
                )
            agent.tools = tools
        else:
            agent.tools = []

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409, detail="Agent name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(agent)

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[t.id for t in agent.tools],
    )


@router.delete("/agents/{agent_id}", status_code=204)
def delete_agent(
    agent_id: int,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.tenant_id == tenant_id,
        )
        .first()
    )

    if not agent:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(agent)
    db.commit()
    return None
