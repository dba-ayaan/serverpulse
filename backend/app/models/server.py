from sqlalchemy import (
    Boolean, Integer, String, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    hostname: Mapped[str] = mapped_column(String(255))
    environment: Mapped[str] = mapped_column(String(30))
    exporter_port: Mapped[int] = mapped_column(Integer, default=9100)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "hostname", "exporter_port",
            name="uq_server_target"
        ),
    )
