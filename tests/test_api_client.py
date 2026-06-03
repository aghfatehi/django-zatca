from django.test import TestCase
from unittest.mock import patch, MagicMock
from django_zatca.services.api_client import ApiClient
from django_zatca.enums import Environment


class ApiClientTestCase(TestCase):
    def test_default_environment(self):
        client = ApiClient()
        self.assertEqual(client.environment, Environment.SANDBOX)

    def test_base_url_sandbox(self):
        client = ApiClient()
        self.assertIn("developer-portal", client.base_url)

    def test_base_url_production(self):
        client = ApiClient(environment=Environment.PRODUCTION)
        self.assertIn("gw-fatoora", client.base_url)

    def test_build_headers_no_auth(self):
        client = ApiClient()
        headers = client._build_headers(None, None, None)
        self.assertIn("Accept-Version", headers)
        self.assertIn("Content-Type", headers)

    def test_build_headers_with_otp(self):
        client = ApiClient()
        headers = client._build_headers(None, None, "123456")
        self.assertEqual(headers["OTP"], "123456")

    def test_build_headers_with_certificate(self):
        client = ApiClient()
        headers = client._build_headers("cert", "secret", None)
        self.assertIn("Authorization", headers)

    @patch("django_zatca.services.api_client.urlopen")
    def test_post_success(self, mock_urlopen):
        mock_resp = MagicMock()
        import json
        mock_resp.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        client = ApiClient()
        response = client.post("/test", {"key": "value"})
        self.assertEqual(response, {"status": "ok"})
