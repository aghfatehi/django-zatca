from django.test import TestCase
from django_zatca.services.qr_code import QRCodeService, generate_phase1_qr
import base64


class QRCodeServiceTestCase(TestCase):
    def test_generate_phase1_qr_non_empty(self):
        result = generate_phase1_qr("Test Co", "311111111100003",
                                    "2024-01-15T14:30:00Z", "115.00", "15.00")
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    def test_generate_phase1_qr_is_base64(self):
        result = generate_phase1_qr("T", "V", "D", "100", "15")
        # should be valid base64
        decoded = base64.b64decode(result)
        self.assertGreater(len(decoded), 5)

    def test_render_returns_string(self):
        service = QRCodeService()
        tlv = generate_phase1_qr("T", "V", "D", "100", "15")
        rendered = service.render(tlv, size=200)
        self.assertIsNotNone(rendered)
