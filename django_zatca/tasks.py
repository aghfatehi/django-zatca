"""
Future Development — Async invoice sync tasks.

Currently dispatched synchronously. Replace the placeholder below
with Celery tasks or Django Q/Huey/background-tasks when wiring
async processing.
"""
import logging
from django_zatca.signals import invoice_cleared, invoice_reported, invoice_failed
from django_zatca.dto import InvoiceDTO, ComplianceResultDTO

logger = logging.getLogger("django_zatca")


def sync_invoice_to_zatca(invoice_data, egs_unit, certificate, private_key, secret):
    from .services.phase2 import Phase2Service

    logger.info(f"Processing invoice sync: {invoice_data.get('invoice_serial_number', 'unknown')}")

    try:
        invoice = InvoiceDTO.from_dict(invoice_data)
        phase2 = Phase2Service()
        signed = phase2.sign_invoice(invoice, egs_unit, certificate, private_key)
        result = phase2.submit_invoice(signed["signed_xml"], signed["invoice_hash"], certificate, secret)

        if result.success:
            from .enums import Environment
            env = Environment(phase2.api_client.environment)
            if env.is_production():
                invoice_cleared.send(sender=sync_invoice_to_zatca, invoice_data=invoice_data, result=result)
            else:
                invoice_reported.send(sender=sync_invoice_to_zatca, invoice_data=invoice_data, result=result)
            logger.info(f"Invoice synced successfully: {invoice.invoice_serial_number}")
        else:
            raise RuntimeError(result.error_message or "Unknown error")

    except Exception as e:
        logger.error(f"Invoice sync failed: {e}")
        invoice_failed.send(sender=sync_invoice_to_zatca, invoice_data=invoice_data, error_message=str(e))
        raise
