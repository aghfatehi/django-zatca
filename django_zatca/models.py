import logging
from django.db import models
from django.utils import timezone

logger = logging.getLogger("django_zatca")


class ZatcaCertificateManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class ZatcaCertificate(models.Model):
    certificate = models.TextField(verbose_name="Certificate")
    private_key = models.TextField(verbose_name="Private Key")
    secret = models.CharField(max_length=255, verbose_name="Secret")
    serial_number = models.CharField(
        max_length=255, blank=True, db_index=True, verbose_name="Serial Number",
    )
    is_active = models.BooleanField(default=False, db_index=True, verbose_name="Active")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expires At")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    objects = ZatcaCertificateManager()

    class Meta:
        db_table = "zatca_certificates"
        verbose_name = "ZATCA Certificate"
        verbose_name_plural = "ZATCA Certificates"
        ordering = ["-created_at"]

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        sn = self.serial_number or "No Serial"
        return f"ZATCA Certificate {sn} ({status})"

    @classmethod
    def deactivate_active_certificates(cls):
        return cls.objects.filter(is_active=True).update(is_active=False)

    def save(self, *args, **kwargs):
        if self.is_active:
            ZatcaCertificate.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ZatcaInvoiceLog(models.Model):
    invoice_serial_number = models.CharField(
        max_length=255, db_index=True, verbose_name="Invoice Serial",
    )
    uuid = models.CharField(
        max_length=255, blank=True, db_index=True, verbose_name="Invoice UUID",
    )
    invoice_hash = models.TextField(blank=True, verbose_name="Invoice Hash")
    signed_xml = models.TextField(blank=True, verbose_name="Signed XML")
    submission_status = models.CharField(
        max_length=50, blank=True, db_index=True, verbose_name="Submission Status",
    )
    clearance_status = models.CharField(
        max_length=50, blank=True, verbose_name="Clearance Status",
    )
    reporting_status = models.CharField(
        max_length=50, blank=True, verbose_name="Reporting Status",
    )
    request_id = models.CharField(
        max_length=255, blank=True, verbose_name="ZATCA Request ID",
    )
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Submitted At")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = "zatca_invoice_logs"
        verbose_name = "ZATCA Invoice Log"
        verbose_name_plural = "ZATCA Invoice Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.invoice_serial_number} - {self.submission_status or 'Pending'}"
