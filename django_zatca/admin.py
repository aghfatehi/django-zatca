from django.contrib import admin
from .models import ZatcaCertificate, ZatcaInvoiceLog


@admin.register(ZatcaCertificate)
class ZatcaCertificateAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "is_active", "created_at", "expires_at")
    list_filter = ("is_active",)
    search_fields = ("serial_number",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ZatcaInvoiceLog)
class ZatcaInvoiceLogAdmin(admin.ModelAdmin):
    list_display = ("invoice_serial_number", "submission_status", "clearance_status", "reporting_status", "submitted_at")
    list_filter = ("submission_status", "clearance_status", "reporting_status")
    search_fields = ("invoice_serial_number", "uuid", "request_id")
    readonly_fields = ("created_at", "updated_at")
