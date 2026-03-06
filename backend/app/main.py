from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="California National Park Visitation Planner API",
    description="Initial FastAPI scaffold for park planning services.",
    version="0.1.0",
)

app.include_router(api_router)
