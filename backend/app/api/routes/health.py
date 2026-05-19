from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check(db: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
