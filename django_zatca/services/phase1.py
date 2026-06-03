import logging
from datetime import datetime
from ..dto import InvoiceDTO
from .qr_code import QRCodeService, generate_phase1_qr

logger = logging.getLogger("django_zatca")


class Phase1Service:
    def __init__(self, qr_service=None):
        self.qr_service = qr_service or QRCodeService()

    def generate_qr_code_text(self, seller_name, vat_number, invoice_date, total_amount, tax_amount):
        return generate_phase1_qr(seller_name, vat_number, invoice_date, total_amount, tax_amount)

    def generate_qr_code_from_invoice(self, invoice, egs_unit):
        invoice_date = datetime.strptime(f"{invoice.issue_date} {invoice.issue_time}", "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        return generate_phase1_qr(
            seller_name=egs_unit.get("vat_name", ""),
            vat_number=egs_unit.get("vat_number", ""),
            invoice_date=invoice_date,
            total_amount=str(self._calculate_total(invoice)),
            tax_amount=str(self._calculate_vat(invoice)),
        )

    def render_qr_code(self, tlv_data, size=200):
        return self.qr_service.render(tlv_data, size)

    def _calculate_total(self, invoice):
        total = 0.0
        for item in invoice.line_items:
            if isinstance(item, dict):
                li = item
            else:
                li = item.to_dict() if hasattr(item, "to_dict") else item
            subtotal = float(li.get("tax_exclusive_price", 0)) * float(li.get("quantity", 0))
            discounts = sum(float(d.get("amount", 0)) for d in li.get("discounts", []))
            taxable = subtotal - discounts
            vat = taxable * float(li.get("vat_percent", 0))
            total += taxable + vat
        return round(total, 2)

    def _calculate_vat(self, invoice):
        vat = 0.0
        for item in invoice.line_items:
            if isinstance(item, dict):
                li = item
            else:
                li = item.to_dict() if hasattr(item, "to_dict") else item
            subtotal = float(li.get("tax_exclusive_price", 0)) * float(li.get("quantity", 0))
            discounts = sum(float(d.get("amount", 0)) for d in li.get("discounts", []))
            taxable = subtotal - discounts
            vat += taxable * float(li.get("vat_percent", 0))
        return round(vat, 2)
