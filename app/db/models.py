from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


agent_tools = sa.Table(
    "agent_tools",
    Base.metadata,
    sa.Column(
        "agent_id",
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "tool_id",
        ForeignKey("tools.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tools_agent_tool"),
)


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tools_tenant_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        secondary=agent_tools,
        back_populates="tools",
    )


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_agents_tenant_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    tools: Mapped[list["Tool"]] = relationship(
        "Tool",
        secondary=agent_tools,
        back_populates="agents",
    )

    # Relationship kept for ORM completeness; deletion is handled by FK(ondelete="CASCADE").
    executions: Mapped[list["AgentExecution"]] = relationship(
        "AgentExecution",
        back_populates="agent",
    )


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")
