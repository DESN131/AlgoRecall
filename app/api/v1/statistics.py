from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.timezone import local_today
from app.schemas.statistics import StatisticsOverview
from app.services.statistics_service import overview

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/overview", response_model=StatisticsOverview)
def statistics_overview(db: Annotated[Session, Depends(get_db)]):
    return overview(db, local_today())

