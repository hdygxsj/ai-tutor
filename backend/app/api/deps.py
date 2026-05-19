from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.tenant import TenantContext
from app.db.session import get_db


def get_tenant_context(settings: Annotated[Settings, Depends(get_settings)]) -> TenantContext:
    return TenantContext(
        tenant_id=settings.default_tenant_id,
        workspace_id=settings.default_workspace_id,
    )


def get_session(db: Annotated[Session, Depends(get_db)]) -> Generator[Session, None, None]:
    yield db
