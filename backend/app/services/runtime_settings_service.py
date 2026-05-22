from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.schemas.runtime import RuntimeSettingsResponse, RuntimeSettingsUpdate
from app.services.workspace_settings_store import WorkspaceSettingsStore

RUNTIME_SETTINGS_KEY = "runtime"


class RuntimeSettingsService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.store = WorkspaceSettingsStore(db, tenant)

    def get_settings(self) -> RuntimeSettingsResponse:
        stored = self.store.get_value(RUNTIME_SETTINGS_KEY)
        if stored is None:
            return self._to_response(RuntimeSettingsUpdate(), kubeconfig=None)
        kubeconfig = stored.pop("kubeconfig", None)
        return self._to_response(RuntimeSettingsUpdate(**stored), kubeconfig=kubeconfig)

    def save_settings(self, update: RuntimeSettingsUpdate) -> RuntimeSettingsResponse:
        current = self._current_update()
        kubeconfig = current.get("kubeconfig")
        saved = RuntimeSettingsUpdate(
            backend=update.backend,
            sandbox_image=update.sandbox_image,
            kubernetes_namespace=update.kubernetes_namespace,
        )
        if update.backend == "sandbox" or update.kubeconfig == "":
            kubeconfig = None
        elif update.kubeconfig and update.kubeconfig.strip():
            kubeconfig = update.kubeconfig

        payload = saved.model_dump()
        if kubeconfig is not None:
            payload["kubeconfig"] = kubeconfig
        self.store.save_value(RUNTIME_SETTINGS_KEY, payload)
        return self._to_response(saved, kubeconfig=kubeconfig)

    def _current_update(self) -> dict[str, str | None]:
        stored = self.store.get_value(RUNTIME_SETTINGS_KEY)
        return stored or {}

    def _to_response(
        self,
        settings: RuntimeSettingsUpdate,
        kubeconfig: str | None,
    ) -> RuntimeSettingsResponse:
        return RuntimeSettingsResponse(
            backend=settings.backend,
            sandbox_image=settings.sandbox_image,
            kubernetes_namespace=settings.kubernetes_namespace,
            has_kubeconfig=bool(kubeconfig and kubeconfig.strip()),
        )
