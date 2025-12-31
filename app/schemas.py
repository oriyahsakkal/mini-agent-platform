from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)


class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1)


class ToolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    tool_ids: list[int] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1)

    # tool_ids semantics:
    # - None  => do not change tools
    # - []    => clear tools
    # - [..]  => replace tools with given list
    tool_ids: list[int] | None = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    description: str
    tool_ids: list[int] = Field(default_factory=list)


class RunAgentRequest(BaseModel):
    task: str = Field(min_length=1)
    model: str = Field(min_length=1)


class RunAgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: int
    model: str
    prompt: str
    response: str
    created_at: datetime


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model: str
    prompt: str
    response: str
    created_at: datetime


class ExecutionListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    limit: int
    offset: int
    items: list[ExecutionOut]
