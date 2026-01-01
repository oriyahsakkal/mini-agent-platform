from app.llm import SUPPORTED_MODELS, mock_llm_complete
from app.rate_limit import check_rate_limit
from app.repositories.runs_repo import RunsRepository
from app.repositories.agents_repo import AgentsRepository
from app.core.errors import BadRequestError


class RunsService:
    def __init__(
        self,
        runs_repo: RunsRepository,
        agents_repo: AgentsRepository,
    ):
        self.runs_repo = runs_repo
        self.agents_repo = agents_repo

    def run(
        self,
        tenant_id: str,
        agent_id: int,
        model: str,
        task: str,
    ):
        try:
            check_rate_limit(tenant_id)
        except RuntimeError as e:
            from app.core.errors import RateLimitError

            raise RateLimitError(str(e))

        if model not in SUPPORTED_MODELS:
            raise BadRequestError("Unsupported model")

        agent = self.agents_repo.get(tenant_id, agent_id)
        if not agent:
            raise BadRequestError("Agent not found")

        tool_names = (
            ", ".join(sorted(t.name for t in agent.tools)) if agent.tools else "none"
        )

        prompt = (
            f"Agent Name: {agent.name}\n"
            f"Role: {agent.role}\n"
            f"Description: {agent.description}\n"
            f"Tools: {tool_names}\n\n"
            f"Task: {task}\n"
            f"Instructions: Respond as the agent, using tools when relevant.\n"
        )

        response = mock_llm_complete(model, prompt)

        return self.runs_repo.create(
            tenant_id=tenant_id,
            agent_id=agent.id,
            model=model,
            prompt=prompt,
            response=response,
        )

    def list_runs(
        self,
        tenant_id: str,
        agent_id: int,
        limit: int,
        offset: int,
    ):
        return self.runs_repo.list(
            tenant_id=tenant_id,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )
