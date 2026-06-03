from django.test import TestCase
from django_zatca.models import ZatcaCertificate, ZatcaInvoiceLog
from datetime import datetime


class ZatcaCertificateTestCase(TestCase):
    def test_create_certificate(self):
        cert = ZatcaCertificate.objects.create(
            certificate="cert-body",
            private_key="key-body",
            secret="my-secret",
            serial_number="SN-001",
            is_active=True,
        )
        self.assertEqual(str(cert), "ZATCA Certificate SN-001 (Active)")
        self.assertTrue(cert.is_active)

    def test_deactivate_active_certificates(self):
        ZatcaCertificate.objects.create(
            certificate="c1", private_key="k1", secret="s1", is_active=True,
        )
        ZatcaCertificate.objects.create(
            certificate="c2", private_key="k2", secret="s2", is_active=True,
        )
        ZatcaCertificate.deactivate_active_certificates()
        self.assertEqual(ZatcaCertificate.objects.filter(is_active=True).count(), 0)


class ZatcaInvoiceLogTestCase(TestCase):
    def test_create_log(self):
        log = ZatcaInvoiceLog.objects.create(
            invoice_serial_number="SER001",
            uuid="uuid-001",
            invoice_hash="abc123",
            submission_status="SUBMITTED",
        )
        self.assertEqual(str(log), "Invoice SER001 - SUBMITTED")
        self.assertIsNotNone(log.created_at)
