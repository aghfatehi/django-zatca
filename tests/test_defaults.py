from django.test import TestCase
from django_zatca.defaults import zatca_setting, get_egs_config


class DefaultsTestCase(TestCase):
    def test_zatca_setting_returns_default(self):
        val = zatca_setting("NONEXISTENT_KEY", "fallback")
        self.assertEqual(val, "fallback")

    def test_get_egs_config_structure(self):
        config = get_egs_config()
        self.assertIn("uuid", config)
        self.assertIn("vat_number", config)
        self.assertIn("vat_name", config)
        self.assertIn("location", config)
        self.assertIsInstance(config["location"], dict)
        self.assertIn("city", config["location"])
        self.assertIn("branch_name", config)
        self.assertIn("branch_industry", config)
