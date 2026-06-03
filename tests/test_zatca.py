from django.test import TestCase
from unittest.mock import patch
from django_zatca.services.zatca import ZatcaService


class ZatcaServiceTestCase(TestCase):
    @patch("django_zatca.services.zatca.zatca_setting")
    def test_default_phase_both(self, mock_setting):
        mock_setting.side_effect = lambda k, d=None: {
            "PHASE": "both", "ENVIRONMENT": "sandbox",
        }.get(k, d)
        service = ZatcaService()
        self.assertTrue(service.is_phase1_enabled())
        self.assertTrue(service.is_phase2_enabled())

    @patch("django_zatca.services.zatca.zatca_setting")
    def test_phase1_only(self, mock_setting):
        mock_setting.side_effect = lambda k, d=None: {
            "PHASE": "phase_1", "ENVIRONMENT": "sandbox",
        }.get(k, d)
        service = ZatcaService()
        self.assertTrue(service.is_phase1_enabled())
        self.assertFalse(service.is_phase2_enabled())

    @patch("django_zatca.services.zatca.zatca_setting")
    def test_phase2_only(self, mock_setting):
        mock_setting.side_effect = lambda k, d=None: {
            "PHASE": "phase_2", "ENVIRONMENT": "production",
        }.get(k, d)
        service = ZatcaService()
        self.assertFalse(service.is_phase1_enabled())
        self.assertTrue(service.is_phase2_enabled())
        self.assertEqual(service.env.value, "production")
