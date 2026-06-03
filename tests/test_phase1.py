from django.test import TestCase
from django_zatca.services.phase1 import Phase1Service
from django_zatca.dto import InvoiceDTO, LineItemDTO


class Phase1ServiceTestCase(TestCase):
    def setUp(self):
        self.service = Phase1Service()

    def test_generate_qr_code_text(self):
        qr = self.service.generate_qr_code_text(
            "Test Co", "311111111100003",
            "2024-01-15T14:30:00Z", "115.00", "15.00",
        )
        self.assertIsNotNone(qr)
        self.assertGreater(len(qr), 0)

    def test_calculate_total(self):
        invoice = InvoiceDTO(
            invoice_serial_number="SER001", invoice_counter_number=1,
            issue_date="2024-01-15", issue_time="14:30:00",
            currency="SAR", previous_invoice_hash="", invoice_type="INVOICE",
            line_items=[
                LineItemDTO(id="1", name="A", quantity=2,
                            tax_exclusive_price=50.00, vat_percent=0.15),
            ],
        )
        total = self.service._calculate_total(invoice)
        # 2 * 50 = 100, vat = 100 * 0.15 = 15, total = 115
        self.assertAlmostEqual(total, 115.00, places=2)

    def test_calculate_vat(self):
        invoice = InvoiceDTO(
            invoice_serial_number="SER001", invoice_counter_number=1,
            issue_date="2024-01-15", issue_time="14:30:00",
            currency="SAR", previous_invoice_hash="", invoice_type="INVOICE",
            line_items=[
                LineItemDTO(id="1", name="A", quantity=2,
                            tax_exclusive_price=50.00, vat_percent=0.15),
            ],
        )
        vat = self.service._calculate_vat(invoice)
        # 2 * 50 = 100, vat = 100 * 0.15 = 15
        self.assertAlmostEqual(vat, 15.00, places=2)
