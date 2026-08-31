from fastapi import APIRouter
from app.api.v1 import problems, reviews, statistics, tags

router = APIRouter(prefix="/api/v1")
router.include_router(problems.router)
router.include_router(reviews.router)
router.include_router(tags.router)
router.include_router(statistics.router)

