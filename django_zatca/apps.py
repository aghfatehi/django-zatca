from django.apps import AppConfig


class DjangoZatcaConfig(AppConfig):
    name = "django_zatca"
    verbose_name = "Django ZATCA (Fatoora)"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django_zatca.signals import (
            invoice_cleared, invoice_reported, invoice_failed,
            invoice_compliance_checked, log_zatca_event,
        )
        invoice_cleared.connect(log_zatca_event, sender=None)
        invoice_reported.connect(log_zatca_event, sender=None)
        invoice_failed.connect(log_zatca_event, sender=None)
        invoice_compliance_checked.connect(log_zatca_event, sender=None)
