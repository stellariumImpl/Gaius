from fastapi import APIRouter
from app.config import config

router=APIRouter()

@router.get("/health")
async def health_check():
    return{
        "code": 200,
        "message": "success",
        "data": {
            "service": config.app_name,
            "version": config.app_version,
            "status": "healthy", # hard-coded
        }
    }