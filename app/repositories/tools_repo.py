from __future__ import annotations

from sqlalchemy.orm import Session
from app.db.models import Tool


class ToolsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, tenant_id: str, name: str, description: str) -> Tool:
        tool = Tool(
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def list_tools(self, tenant_id: str) -> list[Tool]:
        return (
            self.db.query(Tool)
            .filter(Tool.tenant_id == tenant_id)
            .order_by(Tool.id.asc())
            .all()
        )

    def get(self, tenant_id: str, tool_id: int) -> Tool | None:
        return (
            self.db.query(Tool)
            .filter(Tool.tenant_id == tenant_id, Tool.id == tool_id)
            .first()
        )

    def save(self) -> None:
        self.db.commit()

    def delete(self, tool: Tool) -> None:
        self.db.delete(tool)
        self.db.commit()

    def get_many(self, tenant_id: str, tool_ids: list[int]):
        return (
            self.db.query(Tool)
            .filter(
                Tool.tenant_id == tenant_id,
                Tool.id.in_(tool_ids),
            )
            .all()
        )
