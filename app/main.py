from fastapi import FastAPI
from app.api import health
from app.config import config

app=FastAPI(
    title=config.app_name,
    version=config.app_version,
)

app.include_router(health.router,prefix="/api",tags=["health"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {config.app_name}",
        "docs": "/docs",
    }

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )