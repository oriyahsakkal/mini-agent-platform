from fastapi import FastAPI, Depends

from app.deps import get_tenant_id
from app.api.routers.tools import router as tools_router
from app.api.routers.agents import router as agents_router

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
    return {"tenant_id": tenant_id}


app.include_router(tools_router)
app.include_router(agents_router)
