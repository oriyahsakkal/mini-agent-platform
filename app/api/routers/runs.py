from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.error_map import raise_http
from app.deps import get_tenant_id, get_db
from app.schemas import (
    RunAgentRequest,
    RunAgentResponse,
    ExecutionOut,
    ExecutionListOut,
)

from app.repositories.runs_repo import RunsRepository
from app.repositories.agents_repo import AgentsRepository
from app.services.runs_service import RunsService

router = APIRouter(tags=["runs"])


def _service(db: Session) -> RunsService:
    return RunsService(
        RunsRepository(db),
        AgentsRepository(db),
    )


@router.post("/agents/{agent_id}/run", response_model=RunAgentResponse)
def run_agent(
    agent_id: int,
    payload: RunAgentRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    try:
        execution = _service(db).run(
            tenant_id=tenant_id,
            agent_id=agent_id,
            model=payload.model,
            task=payload.task,
        )

        return RunAgentResponse(
            agent_id=execution.agent_id,
            model=execution.model,
            prompt=execution.prompt,
            response=execution.response,
            created_at=execution.created_at,
        )
    except Exception as e:
        raise_http(e)


@router.get("/agents/{agent_id}/runs", response_model=ExecutionListOut)
def list_agent_runs(
    agent_id: int,
    limit: int = 20,
    offset: int = 0,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    try:
        total, rows = _service(db).list_runs(
            tenant_id=tenant_id,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )

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
    except Exception as e:
        raise_http(e)
