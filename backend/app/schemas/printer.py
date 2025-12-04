"""Printer schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.printer import ConnectionTypeEnum, PrinterTypeEnum


class PrinterBase(BaseModel):
    """Base printer schema."""

    name: str = Field(..., min_length=1, max_length=255)
    printer_type: PrinterTypeEnum
    connection_type: ConnectionTypeEnum
    address: str = Field(..., min_length=1, max_length=255)
    label_width_mm: float = Field(..., gt=0)
    label_height_mm: float = Field(..., gt=0)
    is_default: bool = False


class PrinterCreate(PrinterBase):
    """Schema for creating a printer."""

    pass


class PrinterUpdate(BaseModel):
    """Schema for updating a printer."""

    name: str | None = Field(None, min_length=1, max_length=255)
    printer_type: PrinterTypeEnum | None = None
    connection_type: ConnectionTypeEnum | None = None
    address: str | None = Field(None, min_length=1, max_length=255)
    label_width_mm: float | None = Field(None, gt=0)
    label_height_mm: float | None = Field(None, gt=0)
    is_default: bool | None = None


class PrinterResponse(BaseModel):
    """Schema for printer response."""

    id: UUID
    name: str
    printer_type: PrinterTypeEnum
    connection_type: ConnectionTypeEnum
    address: str
    label_width_mm: float
    label_height_mm: float
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LabelData(BaseModel):
    """Data for printing a label."""

    container_id: UUID
    include_contents: bool = False
