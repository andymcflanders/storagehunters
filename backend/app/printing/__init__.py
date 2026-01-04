"""Printing module for label generation."""

from app.models.printer import ConnectionTypeEnum, Printer, PrinterTypeEnum
from app.printing.base import BaseDriver, ItemDetail, LabelContent, PrinterDriver
from app.printing.brother_ql import BrotherQLDriver
from app.printing.network_ipp import NetworkIPPDriver
from app.printing.pdf_generator import PDFLabelDriver
from app.printing.zebra_zpl import ZebraZPLDriver

__all__ = [
    "BaseDriver",
    "ItemDetail",
    "LabelContent",
    "PrinterDriver",
    "ZebraZPLDriver",
    "BrotherQLDriver",
    "PDFLabelDriver",
    "NetworkIPPDriver",
    "get_driver",
]


def get_driver(printer: Printer) -> BaseDriver:
    """
    Get the appropriate driver for a printer configuration.

    Args:
        printer: The printer configuration from the database

    Returns:
        A driver instance configured for the printer
    """
    if printer.printer_type == PrinterTypeEnum.ZEBRA_ZPL:
        return ZebraZPLDriver(
            address=printer.address,
            label_width_mm=printer.label_width_mm,
            label_height_mm=printer.label_height_mm,
        )

    elif printer.printer_type == PrinterTypeEnum.BROTHER_QL:
        return BrotherQLDriver(
            address=printer.address,
            label_width_mm=printer.label_width_mm,
            label_height_mm=printer.label_height_mm,
        )

    elif printer.printer_type == PrinterTypeEnum.GENERIC_PDF:
        return PDFLabelDriver(
            address=printer.address,
            label_width_mm=printer.label_width_mm,
            label_height_mm=printer.label_height_mm,
        )

    elif printer.printer_type == PrinterTypeEnum.NETWORK_IPP:
        return NetworkIPPDriver(
            address=printer.address,
            label_width_mm=printer.label_width_mm,
            label_height_mm=printer.label_height_mm,
        )

    else:
        raise ValueError(f"Unknown printer type: {printer.printer_type}")
