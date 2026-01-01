from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_tenant_id, get_db
from app.db.models import Agent, AgentExecution
from app.schemas import (
    RunAgentRequest,
    RunAgentResponse,
    ExecutionOut,
    ExecutionListOut,
)
from app.llm import SUPPORTED_MODELS, mock_llm_complete
from app.rate_limit import check_rate_limit

router = APIRouter(tags=["runs"])


@router.post("/agents/{agent_id}/run", response_model=RunAgentResponse)
def run_agent(
    agent_id: int,
    payload: RunAgentRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

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


@router.get("/agents/{agent_id}/runs", response_model=ExecutionListOut)
def list_agent_runs(
    agent_id: int,
    limit: int = 20,
    offset: int = 0,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

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
