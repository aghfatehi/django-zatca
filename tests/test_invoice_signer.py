from django.test import TestCase
from unittest.mock import patch, MagicMock, PropertyMock
from django_zatca.dto import InvoiceDTO, LineItemDTO
from django_zatca.services.invoice_signer import InvoiceSignerService
from django_zatca.services import certificate as cert_mod


class InvoiceSignerServiceTestCase(TestCase):
    def setUp(self):
        self.signer = InvoiceSignerService()
        self.egs = {
            "uuid": "test-egs-uuid",
            "vat_number": "311111111100003",
            "vat_name": "Test Co",
            "city": "Riyadh",
            "street": "Olaya",
            "building": "1234",
            "plot_identification": "5678",
            "postal_zone": "12345",
            "branch_name": "Main Branch",
            "branch_industry": "Retail",
            "crn_number": "CRN12345",
        }

    def _make_invoice(self, **kw):
        items = kw.pop("line_items", [
            LineItemDTO(id="1", name="Item", quantity=1,
                        tax_exclusive_price=100.00, vat_percent=0.15),
        ])
        return InvoiceDTO(
            invoice_serial_number=kw.get("serial", "SER001"),
            invoice_counter_number=kw.get("counter", 1),
            issue_date=kw.get("issue_date", "2024-01-15"),
            issue_time=kw.get("issue_time", "14:30:00"),
            currency="SAR",
            previous_invoice_hash="",
            invoice_type="INVOICE",
            line_items=items,
        )

    def test_compute_invoice_hash_returns_string(self):
        from xml.dom import minidom
        doc = minidom.parseString("<Invoice>test</Invoice>")
        h = self.signer._compute_invoice_hash(doc)
        self.assertIsNotNone(h)
        self.assertGreater(len(h), 10)

    @patch("django_zatca.services.certificate.parse_certificate_info")
    @patch.object(InvoiceSignerService, "_create_digital_signature")
    def test_sign_returns_expected_keys(self, mock_sign, mock_parse):
        mock_parse.return_value = {
            "hash": "abc", "issuer": "test", "serial_number": "SN001",
            "public_key": b"key", "signature": "sig",
        }
        mock_sign.return_value = "fake-signature"
        pk = cert_mod.generate_ec_key_pair()
        result = self.signer.sign(
            self._make_invoice(), self.egs, "dummy-cert", pk,
        )
        self.assertIn("signed_xml", result)
        self.assertIn("invoice_hash", result)
        self.assertIn("qr_tlv", result)

    @patch("django_zatca.services.certificate.parse_certificate_info")
    @patch.object(InvoiceSignerService, "_create_digital_signature")
    def test_line_items_in_xml(self, mock_sign, mock_parse):
        mock_parse.return_value = {
            "hash": "abc", "issuer": "test", "serial_number": "SN001",
            "public_key": b"key", "signature": "sig",
        }
        mock_sign.return_value = "fake-signature"
        items = [
            LineItemDTO(id="1", name="Product A", quantity=2,
                        tax_exclusive_price=50.00, vat_percent=0.15),
            LineItemDTO(id="2", name="Product B", quantity=1,
                        tax_exclusive_price=200.00, vat_percent=0.05),
        ]
        pk = cert_mod.generate_ec_key_pair()
        result = self.signer.sign(
            self._make_invoice(line_items=items), self.egs, "dummy-cert", pk,
        )
        self.assertIn("Product A", result["signed_xml"])
        self.assertIn("Product B", result["signed_xml"])
