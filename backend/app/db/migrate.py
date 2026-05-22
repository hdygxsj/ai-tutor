from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import get_settings


def run_migrations() -> None:
    if get_settings().app_env == "test":
        return

    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    command.upgrade(alembic_cfg, "head")
