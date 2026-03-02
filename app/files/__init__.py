"""File management module for uploads/downloads."""

from fastapi import APIRouter

from .api import router

file_router = APIRouter()
file_router.include_router(router)

__all__ = ["file_router"]
