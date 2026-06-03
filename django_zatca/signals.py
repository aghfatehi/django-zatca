import logging
from django.dispatch import Signal

logger = logging.getLogger("django_zatca")

invoice_cleared = Signal()
invoice_reported = Signal()
invoice_failed = Signal()
invoice_compliance_checked = Signal()


def log_zatca_event(sender, **kwargs):
    sig_name = kwargs.pop("signal_name", str(sender))
    event_data = kwargs.get("invoice_data", {})
    serial = event_data.get("invoice_serial_number", "unknown")
    error = kwargs.get("error_message")

    levels = {
        "invoice_cleared": (logging.INFO, f"Invoice cleared: {serial}"),
        "invoice_reported": (logging.INFO, f"Invoice reported: {serial}"),
        "invoice_compliance_checked": (logging.INFO, f"Compliance checked: {serial}"),
        "invoice_failed": (logging.ERROR, f"Invoice failed: {serial} - {error}"),
    }
    level, msg = levels.get(sig_name, (logging.INFO, f"ZATCA event: {serial}"))
    logger.log(level, msg)
