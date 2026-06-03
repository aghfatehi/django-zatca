from django.test import TestCase
from django_zatca.dto import (
    LineItemDTO, InvoiceDTO, ComplianceResultDTO, EgsUnitDTO,
)


class LineItemDTOTestCase(TestCase):
    def test_from_dict(self):
        item = LineItemDTO.from_dict({
            "id": "1", "name": "Test Item",
            "quantity": "2", "tax_exclusive_price": "100.00",
            "vat_percent": "0.15",
        })
        self.assertEqual(item.id, "1")
        self.assertEqual(item.quantity, 2.0)
        self.assertEqual(item.vat_percent, 0.15)

    def test_to_dict(self):
        item = LineItemDTO(
            id="1", name="Test", quantity=2, tax_exclusive_price=100.00,
            vat_percent=0.15,
        )
        d = item.to_dict()
        self.assertEqual(d["id"], "1")
        self.assertEqual(d["vat_percent"], 0.15)


class InvoiceDTOTestCase(TestCase):
    def test_from_dict(self):
        inv = InvoiceDTO.from_dict({
            "invoice_serial_number": "SER001",
            "invoice_counter_number": 1,
            "issue_date": "2024-01-15",
            "issue_time": "14:30:00",
            "currency": "SAR",
            "previous_invoice_hash": "",
            "invoice_type": "INVOICE",
            "line_items": [
                {"id": "1", "name": "Item", "quantity": "1",
                 "tax_exclusive_price": "100.00", "vat_percent": "0.15"},
            ],
        })
        self.assertEqual(inv.invoice_serial_number, "SER001")
        self.assertEqual(inv.issue_date, "2024-01-15")
        self.assertEqual(inv.issue_time, "14:30:00")
        self.assertEqual(len(inv.line_items), 1)

    def test_to_dict(self):
        inv = InvoiceDTO(
            invoice_serial_number="SER001",
            invoice_counter_number=1,
            issue_date="2024-01-15",
            issue_time="14:30:00",
            currency="SAR",
            previous_invoice_hash="",
            invoice_type="INVOICE",
            line_items=[
                LineItemDTO(id="1", name="Item", quantity=1,
                            tax_exclusive_price=100.00, vat_percent=0.15),
            ],
        )
        d = inv.to_dict()
        self.assertEqual(d["invoice_serial_number"], "SER001")
        self.assertEqual(d["issue_date"], "2024-01-15")
        self.assertEqual(d["issue_time"], "14:30:00")


class ComplianceResultDTOTestCase(TestCase):
    def test_from_api_response_success(self):
        result = ComplianceResultDTO.from_api_response({
            "requestID": "REQ001",
            "binarySecurityToken": "dGVzdA==",
            "secret": "abc123",
        })
        self.assertTrue(result.success)
        self.assertEqual(result.request_id, "REQ001")
        self.assertEqual(result.secret, "abc123")
        self.assertIsNone(result.error_message)

    def test_from_api_response_error(self):
        result = ComplianceResultDTO.from_api_response({
            "requestID": "REQ002",
            "errors": [{"message": "Invalid OTP"}],
        })
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Invalid OTP")

    def test_failed_factory(self):
        result = ComplianceResultDTO.failed("Something went wrong")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Something went wrong")


class EgsUnitDTOTestCase(TestCase):
    def test_from_dict_nested(self):
        egs = EgsUnitDTO.from_dict({
            "uuid": "uuid-123",
            "vat_number": "311111111100003",
            "vat_name": "Test Co",
            "location": {"city": "Riyadh", "street": "Olaya", "building": "123"},
            "branch_industry": "Retail",
        })
        self.assertEqual(egs.uuid, "uuid-123")
        self.assertEqual(egs.city, "Riyadh")

    def test_from_dict_flat(self):
        egs = EgsUnitDTO.from_dict({
            "uuid": "uuid-456",
            "vat_number": "311111111100003",
            "vat_name": "Test Co",
            "city": "Jeddah",
            "street": "Corniche",
            "building": "456",
            "branch_industry": "Retail",
        })
        self.assertEqual(egs.city, "Jeddah")
        self.assertEqual(egs.street, "Corniche")

    def test_to_dict(self):
        egs = EgsUnitDTO(
            uuid="uuid-789", vat_number="311111111100003", vat_name="Test Co",
            city="Riyadh", street="Olaya", building="123",
            branch_name="Branch", branch_industry="Retail",
        )
        d = egs.to_dict()
        self.assertIsInstance(d["location"], dict)
        self.assertEqual(d["location"]["city"], "Riyadh")
