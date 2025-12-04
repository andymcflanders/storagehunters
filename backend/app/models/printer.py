"""Printer model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class PrinterTypeEnum(str, enum.Enum):
    """Printer type enumeration."""

    ZEBRA_ZPL = "zebra_zpl"
    BROTHER_QL = "brother_ql"
    GENERIC_PDF = "generic_pdf"


class ConnectionTypeEnum(str, enum.Enum):
    """Connection type enumeration."""

    NETWORK = "network"
    USB = "usb"


class Printer(Base):
    """Printer configuration model."""

    __tablename__ = "printers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    printer_type: Mapped[PrinterTypeEnum] = mapped_column(
        Enum(PrinterTypeEnum), nullable=False
    )
    connection_type: Mapped[ConnectionTypeEnum] = mapped_column(
        Enum(ConnectionTypeEnum), nullable=False
    )
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    label_width_mm: Mapped[float] = mapped_column(Float, nullable=False)
    label_height_mm: Mapped[float] = mapped_column(Float, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
