from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.models.settings import WorkspaceSetting


class WorkspaceSettingsStore:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def get_value(self, key: str) -> dict[str, Any] | None:
        row = self.db.scalar(
            select(WorkspaceSetting).where(
                WorkspaceSetting.key == key,
                WorkspaceSetting.tenant_id == self.tenant.tenant_id,
                WorkspaceSetting.workspace_id == self.tenant.workspace_id,
            )
        )
        if row is None:
            return None
        return dict(row.value)

    def save_value(self, key: str, value: dict[str, Any]) -> dict[str, Any]:
        row = self.db.scalar(
            select(WorkspaceSetting).where(
                WorkspaceSetting.key == key,
                WorkspaceSetting.tenant_id == self.tenant.tenant_id,
                WorkspaceSetting.workspace_id == self.tenant.workspace_id,
            )
        )
        if row is None:
            row = WorkspaceSetting(
                tenant_id=self.tenant.tenant_id,
                workspace_id=self.tenant.workspace_id,
                key=key,
                value=value,
            )
            self.db.add(row)
        else:
            row.value = value
        self.db.commit()
        self.db.refresh(row)
        return dict(row.value)
