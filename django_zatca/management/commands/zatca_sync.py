from django.core.management.base import BaseCommand, CommandError
from django_zatca.defaults import zatca_setting, get_egs_config


class Command(BaseCommand):
    help = "Sync pending invoices to ZATCA FATOORA platform"

    def add_arguments(self, parser):
        parser.add_argument("--invoice", type=str, help="Single invoice serial number to sync")
        parser.add_argument("--all", action="store_true", help="Sync all pending invoices")

    def handle(self, *args, **options):
        from django_zatca.services.phase2 import Phase2Service
        from django_zatca.dto import InvoiceDTO

        self.stdout.write(self.style.SUCCESS("ZATCA Invoice Sync\n"))

        certificate = zatca_setting("CERTIFICATE")
        private_key = zatca_setting("PRIVATE_KEY")
        secret = zatca_setting("SECRET")

        if not certificate or not private_key or not secret:
            self.stdout.write(self.style.ERROR("ZATCA credentials not configured."))
            self.stdout.write("Run python manage.py zatca_onboard first.")
            return

        self.stdout.write(f"Using environment: {zatca_setting('ENVIRONMENT', 'sandbox')}\n")

        egs_unit = get_egs_config()

        if options.get("invoice"):
            self._sync_single(options["invoice"], egs_unit, certificate, private_key, secret)
        elif options.get("all"):
            self.stdout.write(self.style.WARNING(
                "Implement your own invoice retrieval logic for --all."
            ))
        else:
            self.stdout.write(self.style.ERROR("Specify --invoice=SERIAL or --all"))

    def _sync_single(self, serial, egs_unit, certificate, private_key, secret):
        from datetime import date, datetime
        from django_zatca.jobs import sync_invoice_to_zatca

        self.stdout.write(f"Dispatching sync job for invoice: {serial}")

        invoice_data = {
            "invoice_serial_number": serial,
            "invoice_counter_number": 1,
            "issue_date": date.today().isoformat(),
            "issue_time": datetime.now().strftime("%H:%M:%S"),
            "currency": "SAR",
            "previous_invoice_hash": "",
            "invoice_type": "INVOICE",
            "line_items": [],
        }

        sync_invoice_to_zatca(invoice_data, egs_unit, certificate, private_key, secret)
        self.stdout.write(self.style.SUCCESS("Sync job dispatched."))
