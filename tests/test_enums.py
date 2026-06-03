from django.test import TestCase
from django_zatca.enums import ZatcaPhase, Environment, InvoiceType, Currency


class EnumsTestCase(TestCase):
    def test_zatca_phase_values(self):
        self.assertEqual(ZatcaPhase.PHASE1.value, "phase_1")
        self.assertEqual(ZatcaPhase.PHASE2.value, "phase_2")
        self.assertEqual(ZatcaPhase.BOTH.value, "both")

    def test_environment_values(self):
        self.assertEqual(Environment.SANDBOX.value, "sandbox")
        self.assertEqual(Environment.PRODUCTION.value, "production")

    def test_environment_is_sandbox(self):
        e = Environment("sandbox")
        self.assertTrue(e.is_sandbox())
        self.assertFalse(e.is_production())

    def test_environment_is_production(self):
        e = Environment("production")
        self.assertTrue(e.is_production())
        self.assertFalse(e.is_sandbox())

    def test_invoice_type_values(self):
        self.assertEqual(InvoiceType.INVOICE.value, "INVOICE")
        self.assertEqual(InvoiceType.CREDIT_NOTE.value, "CREDIT_NOTE")
        self.assertEqual(InvoiceType.DEBIT_NOTE.value, "DEBIT_NOTE")

    def test_currency_values(self):
        self.assertEqual(Currency.SAR.value, "SAR")
