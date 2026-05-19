from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


import app.models.learning  # noqa: E402,F401
