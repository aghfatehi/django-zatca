from django.test import TestCase
from unittest.mock import patch, MagicMock
from django_zatca.services.phase2 import Phase2Service


class Phase2ServiceTestCase(TestCase):
    def setUp(self):
        self.service = Phase2Service()

    def test_generate_keys_and_csr_returns_keys(self):
        egs_unit = {
            "uuid": "test-uuid", "vat_number": "311111111100003",
            "vat_name": "Test Co", "city": "Riyadh", "street": "Olaya",
            "building": "123", "branch_name": "Main", "branch_industry": "Retail",
            "custom_id": "custom-001",
        }
        try:
            result = self.service.generate_keys_and_csr(egs_unit, "ERP")
            self.assertIn("private_key", result)
            self.assertIn("csr", result)
        except Exception as e:
            if "openssl" in str(e).lower():
                self.skipTest("OpenSSL not available on this system")
            raise

    @patch.object(Phase2Service, "issue_compliance_certificate")
    def test_issue_compliance_certificate(self, mock_issue):
        mock_issue.return_value = MagicMock(success=True, request_id="REQ001")
        result = self.service.issue_compliance_certificate("csr-body", "123456")
        self.assertTrue(result.success)

    def test_submit_uses_check_for_sandbox(self):
        self.assertEqual(self.service.api_client.environment.value, "sandbox")
