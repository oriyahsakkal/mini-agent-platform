from fastapi import FastAPI, Depends, HTTPException
from .deps import get_tenant_id, get_db

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .db.models import Tool, Agent, AgentExecution
from .schemas import (
    ToolCreate,
    ToolUpdate,
    ToolOut,
    AgentCreate,
    AgentUpdate,
    AgentOut,
    RunAgentRequest,
    RunAgentResponse,
    ExecutionOut,
    ExecutionListOut,
)

from .llm import SUPPORTED_MODELS, mock_llm_complete

from .rate_limit import check_rate_limit


app = FastAPI(
    title="Mini Agent Platform",
    description="Multi-tenant Agent Platform with Tools, Agents, deterministic mock LLM execution and run history.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Mini Agent Platform is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/whoami")
def whoami(tenant_id: str = Depends(get_tenant_id)):
    """Return the tenant_id resolved from the API key."""
    return {"tenant_id": tenant_id}


@app.post("/tools", response_model=ToolOut, status_code=201)
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
        raise HTTPException(
            status_code=409,
            detail="Tool name already exists for this tenant",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(tool)
    return tool


@app.get("/tools", response_model=list[ToolOut])
def list_tools(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    tools = (
        db.query(Tool).filter(Tool.tenant_id == tenant_id).order_by(Tool.id.asc()).all()
    )
    return tools


@app.get("/tools/{tool_id}", response_model=ToolOut)
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
        raise HTTPException(status_code=404, detail="Tool not found")

    return tool


@app.put("/tools/{tool_id}", response_model=ToolOut)
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
        raise HTTPException(status_code=404, detail="Tool not found")

    if payload.name is not None:
        tool.name = payload.name
    if payload.description is not None:
        tool.description = payload.description

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Tool name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(tool)
    return tool


@app.delete("/tools/{tool_id}", status_code=204)
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
        raise HTTPException(status_code=404, detail="Tool not found")

    db.delete(tool)
    db.commit()
    return None


@app.post("/agents", response_model=AgentOut, status_code=201)
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
            raise HTTPException(
                status_code=400, detail="One or more tools not found for this tenant"
            )

        agent.tools = tools

    db.add(agent)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Agent name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(agent)

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[tool.id for tool in agent.tools],
    )


@app.get("/agents", response_model=list[AgentOut])
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


@app.get("/agents/{agent_id}", response_model=AgentOut)
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
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[t.id for t in agent.tools],
    )


@app.put("/agents/{agent_id}", response_model=AgentOut)
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
        raise HTTPException(
            status_code=409, detail="Agent name already exists for this tenant"
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    db.refresh(agent)

    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tool_ids=[t.id for t in agent.tools],
    )


@app.delete("/agents/{agent_id}", status_code=204)
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
        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(agent)
    db.commit()
    return None


@app.post("/agents/{agent_id}/run", response_model=RunAgentResponse)
def run_agent(
    agent_id: int,
    payload: RunAgentRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    # Per-tenant rate limiting (in-memory): 5 requests / 60 seconds.
    # Exceeding the quota returns HTTP 429.
    try:
        check_rate_limit(tenant_id)
    except RuntimeError:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if payload.model not in SUPPORTED_MODELS:
        raise HTTPException(status_code=400, detail="Unsupported model")

    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            Agent.tenant_id == tenant_id,
        )
        .first()
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tool_names = (
        ", ".join(sorted([t.name for t in agent.tools])) if agent.tools else "none"
    )

    prompt = (
        f"Agent Name: {agent.name}\n"
        f"Role: {agent.role}\n"
        f"Description: {agent.description}\n"
        f"Tools: {tool_names}\n\n"
        f"Task: {payload.task}\n"
        f"Instructions: Respond as the agent, using tools when relevant.\n"
    )

    response_text = mock_llm_complete(payload.model, prompt)

    execution = AgentExecution(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model=payload.model,
        prompt=prompt,
        response=response_text,
    )

    db.add(execution)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    db.refresh(execution)

    return RunAgentResponse(
        agent_id=agent.id,
        model=execution.model,
        prompt=execution.prompt,
        response=execution.response,
        created_at=execution.created_at,
    )


@app.get("/agents/{agent_id}/runs", response_model=ExecutionListOut)
def list_agent_runs(
    agent_id: int,
    limit: int = 20,
    offset: int = 0,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.tenant_id == tenant_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    base_query = (
        db.query(AgentExecution)
        .filter(
            AgentExecution.tenant_id == tenant_id,
            AgentExecution.agent_id == agent_id,
        )
        .order_by(AgentExecution.created_at.desc())
    )

    total = base_query.count()
    rows = base_query.offset(offset).limit(limit).all()

    return ExecutionListOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            ExecutionOut(
                id=e.id,
                model=e.model,
                prompt=e.prompt,
                response=e.response,
                created_at=e.created_at,
            )
            for e in rows
        ],
    )
