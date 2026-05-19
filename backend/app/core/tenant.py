from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    workspace_id: str
