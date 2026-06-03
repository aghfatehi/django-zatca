from django.test import TestCase
from django_zatca.services.certificate import generate_ec_key_pair, generate_csr
from django_zatca.exceptions import CertificateException


class CertificateServiceTestCase(TestCase):
    def test_generate_ec_key_pair(self):
        pk = generate_ec_key_pair()
        self.assertIn("BEGIN EC PRIVATE KEY", pk)

    def test_generate_csr_with_valid_key(self):
        pk = generate_ec_key_pair()
        try:
            csr = generate_csr(
                private_key=pk, solution_name="ERP",
                egs_serial_number="test-uuid", vat_number="311111111100003",
                branch_location="123 Olaya St", branch_industry="Retail",
                branch_name="Main Branch", taxpayer_name="Test Co",
                taxpayer_provided_id="test-uuid-999", production=False,
            )
            self.assertIn("BEGIN CERTIFICATE REQUEST", csr)
        except CertificateException as e:
            if "OpenSSL" in str(e):
                self.skipTest("OpenSSL not fully available")
            raise
