# django-zatca

**ZATCA (Fatoora) e-invoicing integration for Django — Saudi Arabia VAT e-invoicing**

[![PyPI Version](https://img.shields.io/pypi/v/django-zatca?label=PyPI&color=blue)](https://pypi.org/project/django-zatca/)
[![Django](https://img.shields.io/badge/Django-2.2%20|%203.2%20|%204.2%20|%205.0%20|%205.1-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://python.org)
[![License](https://img.shields.io/github/license/aghfatehi/django-zatca)](LICENSE)

معالجة الفوترة الإلكترونية وفق متطلبات هيئة الزكاة والضريبة والجمارك (zatca) - نظام فاتورة

---

## Features

- **Phase 1** — Simplified e-invoicing (QR code generation with TLV encoding)
- **Phase 2** — Full e-invoicing (EC key pair & CSR generation, XML signing, compliance/certificate issuance, clearance & reporting)
- **Pure Python SVG QR** — No external QR library required; built-in pure-Python QR generator
- **Django models** — `ZatcaCertificate` and `ZatcaInvoiceLog` for audit trail
- **Management commands** — `zatca_onboard`, `zatca_sync`, `zatca_check`
- **REST API endpoints** — `/zatca/status`, `/zatca/onboard`, `/zatca/invoice/sync`
- **Signals** — `invoice_cleared`, `invoice_reported`, `invoice_failed` for extensibility

## Requirements

- Python 3.7+
- Django 2.2+

## Quick Start

### 1. Install

```bash
pip install django-zatca
```

### 2. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "django_zatca",
]
```

### 3. Configure

Add `ZATCA` to your Django settings:

```python
ZATCA = {
    "PHASE": "both",                  # "phase1", "phase2", or "both"
    "ENVIRONMENT": "sandbox",         # "sandbox" or "production"
    "EGS_UUID": "your-egs-uuid",
    "VAT_NUMBER": "311111111100003",
    "VAT_NAME": "Your Company Name",
    "CITY": "Riyadh",
    "CITY_SUBDIVISION": "Al Olaya",
    "STREET": "King Fahd Road",
    "BUILDING": "1234",
    "PLOT_IDENTIFICATION": "5678",
    "POSTAL_ZONE": "12345",
    "BRANCH_NAME": "Main Branch",
    "BRANCH_INDUSTRY": "Retail",
    "CRN_NUMBER": "CRN12345",
    "CERTIFICATE": "",                # base64-encoded compliance certificate
    "PRIVATE_KEY": "",                # base64-encoded EC private key
    "SECRET": "",                     # secret from ZATCA
    "QUEUE_CONNECTION": "sync",
    "QUEUE_NAME": "zatca",
    "LOGGING_ENABLED": True,
    "LOG_CHANNEL": "zatca",
    "API_SANDBOX_BASE": "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal",
    "API_PRODUCTION_BASE": "https://gw-fatoora.zatca.gov.sa/e-invoicing/core",
}
```

Or use environment variables with prefix `ZATCA_`:

```bash
export ZATCA_PHASE=both
export ZATCA_ENVIRONMENT=sandbox
export ZATCA_VAT_NUMBER=311111111100003
```

### 4. Run migrations

```bash
python manage.py migrate django_zatca
```

### 5. Generate QR code

```python
from django_zatca.services.qr_code import generate_phase1_qr
from django_zatca.services.svg_qr import SvgQrGenerator

tlv = generate_phase1_qr("Company Name", "311111111100003", "2024-01-15T14:30:00Z", "115.00", "15.00")
svg = SvgQrGenerator().encode(tlv, size=200)
# save svg bytes to file or return as HTTP response
```

### 6. Onboard (Phase 2)

```bash
python manage.py zatca_onboard --otp=123456 --save
```

### 7. Submit invoices

```python
from django_zatca.tasks import sync_invoice_to_zatca

sync_invoice_to_zatca(
    invoice_data={
        "invoice_serial_number": "SER001",
        "invoice_counter_number": 1,
        "issue_date": "2024-01-15",
        "issue_time": "14:30:00",
        "currency": "SAR",
        "previous_invoice_hash": "",
        "invoice_type": "INVOICE",
        "line_items": [
            {"id": "1", "name": "Item", "quantity": "1", "tax_exclusive_price": "100.00", "vat_percent": "0.15"},
        ],
    },
    egs_unit=egs_config,
    certificate=certificate,
    private_key=private_key,
    secret=secret,
)
```

## API Endpoints

Include the URLs in your project:

```python
from django.urls import include, path

urlpatterns = [
    path("api/", include("django_zatca.urls")),
]
```

| Endpoint | Method | Description |
|---|---|---|
| `/api/zatca/status` | GET | Returns phase & environment status |
| `/api/zatca/onboard` | POST | Onboard EGS unit (requires `otp` in JSON body) |
| `/api/zatca/invoice/sync` | POST | Submit an invoice for clearance/reporting |

## Management Commands

| Command | Description |
|---|---|
| `python manage.py zatca_onboard` | Interactive onboarding wizard |
| `python manage.py zatca_sync --invoice=SERIAL` | Sync a single invoice |
| `python manage.py zatca_check` | Check package readiness |

## Signals

```python
from django_zatca.signals import invoice_cleared, invoice_reported, invoice_failed

@receiver(invoice_cleared)
def on_invoice_cleared(sender, invoice_data, result, **kwargs):
    # update your local db status
    pass
```

## Development

```bash
git clone https://github.com/aghfatehi/django-zatca.git
cd django-zatca
pip install -e .
pip install -r requirements-dev.txt
pytest
```

## License

MIT
