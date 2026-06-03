from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ZatcaInvoiceLog",
            fields=[
                ("invoice_serial_number", models.CharField(db_index=True, max_length=255, verbose_name="Invoice Serial")),
                ("uuid", models.CharField(blank=True, db_index=True, max_length=255, verbose_name="Invoice UUID")),
                ("invoice_hash", models.TextField(blank=True, verbose_name="Invoice Hash")),
                ("signed_xml", models.TextField(blank=True, verbose_name="Signed XML")),
                ("submission_status", models.CharField(blank=True, db_index=True, max_length=50, verbose_name="Submission Status")),
                ("clearance_status", models.CharField(blank=True, max_length=50, verbose_name="Clearance Status")),
                ("reporting_status", models.CharField(blank=True, max_length=50, verbose_name="Reporting Status")),
                ("request_id", models.CharField(blank=True, max_length=255, verbose_name="ZATCA Request ID")),
                ("error_message", models.TextField(blank=True, verbose_name="Error Message")),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="Submitted At")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
            ],
            options={
                "verbose_name": "ZATCA Invoice Log",
                "verbose_name_plural": "ZATCA Invoice Logs",
                "db_table": "zatca_invoice_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ZatcaCertificate",
            fields=[
                ("certificate", models.TextField(verbose_name="Certificate")),
                ("private_key", models.TextField(verbose_name="Private Key")),
                ("secret", models.CharField(max_length=255, verbose_name="Secret")),
                ("serial_number", models.CharField(blank=True, db_index=True, max_length=255, verbose_name="Serial Number")),
                ("is_active", models.BooleanField(db_index=True, default=False, verbose_name="Active")),
                ("expires_at", models.DateTimeField(blank=True, null=True, verbose_name="Expires At")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
            ],
            options={
                "verbose_name": "ZATCA Certificate",
                "verbose_name_plural": "ZATCA Certificates",
                "db_table": "zatca_certificates",
                "ordering": ["-created_at"],
            },
        ),
    ]
