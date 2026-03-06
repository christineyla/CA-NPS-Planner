from fastapi import FastAPI

from app.api.router import api_router
from app.core_error_handlers import register_exception_handlers

app = FastAPI(
    title="California National Park Visitation Planner API",
    description="Initial FastAPI scaffold for park planning services.",
    version="0.1.0",
)

register_exception_handlers(app)
app.include_router(api_router)
