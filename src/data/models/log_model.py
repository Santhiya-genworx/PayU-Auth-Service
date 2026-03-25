from __future__ import annotations

from enum import Enum as PyEnum
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.database import Base

if TYPE_CHECKING:
    from src.data.models.user_model import User


class Methods(PyEnum):
    post = "POST"
    put = "PUT"
    delete = "DELETE"


class Logs(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[Methods] = mapped_column(Enum(Methods, name="method_enum", create_type=False))
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    request_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[int] = mapped_column(nullable=False)
    time_taken: Mapped[float] = mapped_column(Numeric, nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="logs")