<p align="center">
    <a href="https://pypi.org/project/django-zatca/"><img src="https://img.shields.io/pypi/v/django-zatca?label=PyPI&color=blue" alt="PyPI Version"></a>
    <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-2.2%20|%203.2%20|%204.2%20|%205.0%20|%205.1%20|%205.2%20|%206.0-green.svg" alt="Django"></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue.svg" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
    <a href="https://github.com/aghfatehi"><img src="https://img.shields.io/badge/Author-AL--AGHBARI%20Fatehi-blue" alt="Author"></a>
</p>

<h1 align="center">Django ZATCA (Fatoora)</h1>
<h3 align="center">Saudi Arabian e-Invoicing Compliance — Phase 1 & Phase 2</h3>
<h3 align="center">المرحلة الأولى والثانية للفاتورة الإلكترونية السعودية لهيئة الزكاة والضريبة والجمارك</h3>
<h4 align="center">By <a href="https://github.com/aghfatehi">AL-AGHBARI Fatehi</a> — <strong>فتحي الأغبري</strong></h4>

<p align="center">
    <strong>ZATCA integration for Django — QR code generation, TLV encoding, invoice signing, clearance & reporting. دمج الفاتورة الإلكترونية مع جانغو: المرحلة الأولى (QR) والمرحلة الثانية (التوقيع والإرسال) لهيئة الزكاة والضريبة والجمارك السعودية</strong>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Version Matrix](#version-matrix)
- [Installation](#installation)
- [Configuration](#configuration)
- [Phase 1 -- QR Code Generation](#phase-1--qr-code-generation-basic-compliance)
- [Phase 2 -- FATOORA API Integration](#phase-2--fatoora-api-integration-full-compliance)
- [QR Code Display on PDF / View](#qr-code-display-on-pdf--view)
- [API Endpoints](#api-endpoints)
- [Management Commands](#management-commands)
- [Signals](#signals)
- [Testing](#testing)
- [Support](#support)

---

## Overview

**django-zatca** is a production-grade Django package for integrating with the **ZATCA (Zakat, Tax and Customs Authority)** e-invoicing system — also known as **Fatoora** — in the Kingdom of Saudi Arabia.

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Generate and display QR code on invoices (TLV Base64 format) | Production Ready |
| **Phase 2** | Full compliance: CSR, Certificate, Signing, Clearance & Reporting via FATOORA API | Production Ready |

### What is Required vs Optional

**For Phase 1 (QR generation only):**
| Step | Required? |
|------|-----------|
| Install package (`pip install django-zatca`) | **Required** |
| Add `django_zatca` to `INSTALLED_APPS` | **Required** |
| Configure `ZATCA` in Django settings | **Required** |
| Call `generate_phase1_qr()` or `QRCodeService().render()` in your view | **Required** |
| Display QR in your template | **Required** |
| Install `segno` or `qrcode[pil]` for ZATCA-compatible QR | Optional but **recommended** |
| API Endpoints | Optional — not needed |
| Management Commands | Optional — not needed |

**For Phase 2 (API integration):**
| Step | Required? |
|------|-----------|
| Everything from Phase 1 | **Required** (if using `both`) |
| Set `PHASE` to `phase2` or `both` | **Required** |
| Complete onboarding (keys + CSR + certificate) | **Required** |
| Call `sign_invoice()` + `submit_invoice()` | **Required** |
| Run migrations for audit logging | Optional |
| Use async tasks | Optional |

---

## Features

- **Phase 1**: TLV Base64 QR code (5 tags: Seller, VAT, Date, Total, Tax)
- **Phase 2**: UBL 2.1 XML invoice building & XAdES signing
- **Phase 2**: ECDSA secp256k1 key pair generation (OpenSSL)
- **Phase 2**: CSR generation for ZATCA compliance certificate
- **Phase 2**: Compliance check (Sandbox)
- **Phase 2**: Clearance & Reporting (Production)
- **Multiple QR backends**: Auto-detects `segno`, `qrcode[pil]`, or built-in fallback
- **Offline invoice preparation** with async sync
- **Management commands** for onboarding & syncing
- **Signals** (InvoiceCleared, InvoiceReported, InvoiceFailed)
- **Logging** with PII masking
- **Pure Python** — no external QR library required (but recommended for ZATCA compatibility)

---

## Version Matrix

| Component | Version |
|-----------|---------|
| **Python** | `^3.7`, `^3.8`, `^3.9`, `^3.10`, `^3.11`, `^3.12`, `^3.13` |
| **Django** | `^2.2`, `^3.2`, `^4.0`, `^5.0`, `^5.1`, `^5.2`, `^6.0` |
| **ZATCA API** | V2 (2024+) |
| **UBL Standard** | 2.1 |
| **Signature Algorithm** | ECDSA secp256k1 + SHA-256 |
| **XAdES** | EPES v1.3.2 |
| **QR Encoding** | TLV Base64 (GS1-compatible) |
| **OpenSSL** | Required (for key & CSR generation) |

### Optional QR Dependencies

The built-in QR generator (`SvgQrGenerator`) produces **visual-only output** that is **not** compatible with the official ZATCA (Fatoora) app. For production use, you **must** install one of these:

| Package | Purpose | Install |
|---------|---------|---------|
| `segno` | ✅ ZATCA-compatible SVG QR (pure Python, no extra deps) | `pip install segno` |
| `qrcode` + `Pillow` | ✅ ZATCA-compatible PNG QR | `pip install qrcode[pil]` |

If one of these is installed, the package uses it automatically. If neither is installed, the built-in fallback produces a QR image that will **not** be readable by the ZATCA app.

---

## Installation

```bash
pip install django-zatca
```

**For ZATCA-compatible QR codes** (recommended):
```bash
pip install django-zatca segno
```
Or:
```bash
pip install django-zatca qrcode[pil]
```

### Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    "django_zatca",
]
```

### Run Migrations (required for Phase 2)

```bash
python manage.py migrate django_zatca
```

### Verify Installation

```bash
python manage.py zatca_check
```

---

## Configuration

Add `ZATCA` to your Django settings:

```python
ZATCA = {
    "PHASE": "both",              # "phase1", "phase2", or "both"
    "ENVIRONMENT": "sandbox",     # "sandbox" or "production"
    "VAT_NUMBER": "311111111100003",
    "VAT_NAME": "Your Company Name",
    ...
}
```

Or use environment variables with prefix `ZATCA_`:

```bash
export ZATCA_PHASE=both
export ZATCA_ENVIRONMENT=sandbox
export ZATCA_VAT_NUMBER=311111111100003
```

### Full Settings Reference

| Setting | ENV Variable | Required | Description |
|---------|-------------|----------|-------------|
| `PHASE` | `ZATCA_PHASE` | Yes | `phase1`, `phase2`, or `both` |
| `ENVIRONMENT` | `ZATCA_ENVIRONMENT` | Yes | `sandbox` or `production` |
| `EGS_UUID` | `ZATCA_EGS_UUID` | Phase 2 | Unique ID for your ERP system |
| `VAT_NUMBER` | `ZATCA_VAT_NUMBER` | Yes | 15-digit Saudi VAT number |
| `VAT_NAME` | `ZATCA_VAT_NAME` | Yes | Company legal name |
| `CRN_NUMBER` | `ZATCA_CRN_NUMBER` | Phase 2 | Commercial Registration Number |
| `INDUSTRY` | `ZATCA_INDUSTRY` | Phase 2 | Business industry (e.g., Retail) |
| `CITY` | `ZATCA_CITY` | Phase 2 | City name |
| `CITY_SUBDIVISION` | `ZATCA_CITY_SUBDIVISION` | Phase 2 | City district |
| `STREET` | `ZATCA_STREET` | Phase 2 | Street name |
| `BUILDING` | `ZATCA_BUILDING` | Phase 2 | Building number |
| `PLOT_ID` | `ZATCA_PLOT_ID` | Phase 2 | Plot identification |
| `POSTAL_ZONE` | `ZATCA_POSTAL_ZONE` | Phase 2 | Postal/ZIP code |
| `BRANCH_NAME` | `ZATCA_BRANCH_NAME` | Phase 2 | Branch name |
| `CERTIFICATE` | `ZATCA_CERTIFICATE` | Phase 2 | Base64 compliance certificate |
| `PRIVATE_KEY` | `ZATCA_PRIVATE_KEY` | Phase 2 | Base64 EC private key |
| `SECRET` | `ZATCA_SECRET` | Phase 2 | Secret from ZATCA onboarding |

### Onboarding Flow

```
1. Run:  python manage.py zatca_onboard --otp=123456 --save
2. Package generates EC key pair (private_key + public_key)
3. Package creates a CSR (Certificate Signing Request)
4. Package sends CSR + OTP to ZATCA API
5. ZATCA returns:
   - binarySecurityToken → save as CERTIFICATE
   - secret              → save as SECRET
6. Your private_key      → save as PRIVATE_KEY
```

The OTP is obtained from the [ZATCA Developer Portal](https://sandbox.zatca.gov.sa) (sandbox) or ZATCA production portal.

---

## Phase 1 -- QR Code Generation (Basic Compliance)

Phase 1 requires **no API calls**. It generates a TLV-encoded Base64 QR string containing:

| Tag | Field | Example |
|-----|-------|---------|
| 1 | Seller Name | `شركة التقنية` |
| 2 | VAT Number | `300000000000003` |
| 3 | Date/Time (ISO 8601) | `2024-01-01T12:00:00Z` |
| 4 | Invoice Total (SAR) | `115.00` |
| 5 | VAT Total (SAR) | `15.00` |

### Simple Usage

```python
from django_zatca.services.qr_code import generate_phase1_qr

tlv = generate_phase1_qr(
    seller_name="شركة التقنية",
    vat_number="300000000000003",
    invoice_date="2024-01-01T12:00:00Z",
    total_amount="115.00",
    tax_amount="15.00",
)
# tlv is a Base64-encoded TLV string ready for QR rendering
```

---

## Phase 2 -- FATOORA API Integration (Full Compliance)

### Step 1: Onboarding

```bash
python manage.py zatca_onboard --otp=123456 --save
```

Or programmatically:

```python
from django_zatca.services.phase2 import Phase2Service
from django_zatca.defaults import get_egs_config

phase2 = Phase2Service()
egs_unit = get_egs_config()
keys = phase2.generate_keys_and_csr(egs_unit, "ERP")
compliance = phase2.issue_compliance_certificate(keys["csr"], "123456")
```

### Step 2: Sign & Submit Invoice

```python
from django_zatca.dto import InvoiceDTO
from django_zatca.defaults import get_egs_config
from django_zatca.services.phase2 import Phase2Service

invoice = InvoiceDTO.from_dict({
    "invoice_serial_number": "INV-001",
    "invoice_counter_number": 1,
    "issue_date": "2024-01-15",
    "issue_time": "14:30:00",
    "line_items": [
        {"id": "1", "name": "Product", "quantity": 1,
         "tax_exclusive_price": "100.00", "vat_percent": 0.15},
    ],
})

phase2 = Phase2Service()
egs_unit = get_egs_config()

# Sign
signed = phase2.sign_invoice(invoice, egs_unit, certificate, private_key)

# Submit
result = phase2.submit_invoice(
    signed["signed_xml"], signed["invoice_hash"],
    certificate, secret,
)
```

---

## QR Code Display on PDF / View

### Method 1: Using the Built-in Template Tag

The package ships with a `{% zatca_qr %}` template tag that **auto-detects** the available QR library:

| Priority | Library | Output | ZATCA Compatible | Install |
|----------|---------|--------|------------------|---------|
| 1st | `segno` | SVG | ✅ Yes | `pip install segno` |
| 2nd | `qrcode` + `SvgImage` | SVG | ✅ Yes | `pip install qrcode` |
| 3rd | `qrcode` + `Pillow` | PNG | ✅ Yes | `pip install qrcode[pil]` |
| 4th | Built-in `SvgQrGenerator` (fallback) | SVG | ❌ No | Not needed (but avoid for production) |

> **⚠️ Important:** The built-in `SvgQrGenerator` is a **visual-only fallback** for development previews. It does **not** produce QR codes that the official ZATCA (Fatoora) app can scan. You **must** install `segno` or `qrcode[pil]` for ZATCA-compliant QR codes.

**In your view:**
```python
from django_zatca.services.qr_code import generate_phase1_qr

def invoice_view(request, invoice_id):
    invoice = get_invoice(invoice_id)
    qr_data = generate_phase1_qr(
        seller_name=invoice.company_name,
        vat_number=invoice.vat_number,
        invoice_date=invoice.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        total_amount=str(invoice.total),
        tax_amount=str(invoice.tax),
    )
    return render(request, "invoice.html", {"qr_data": qr_data})
```

**In your template:**
```django
{% load zatca_qr %}

<div class="qr-section" style="text-align: center; margin-top: 20px;">
    {% zatca_qr qr_data size=200 %}
</div>
```

### Phase 2 QR Code (9 Tags)

Phase 1 QR contains 5 tags (seller name, VAT, date, total, tax). When scanned with the ZATCA (Fatoora) app, it displays a notice: *"This code is not compatible with Phase 2"* — this is **normal** for Phase 1 QR.

For full Phase 2 compliance, the QR must contain **9 tags** including the invoice hash and digital signature. Generate it **after signing the invoice**:

```python
from django_zatca.services.qr_code import generate_phase2_qr

qr_data = generate_phase2_qr(
    seller_name=invoice.company_name,
    vat_number=invoice.vat_number,
    invoice_date=invoice.date.strftime("%Y-%m-%dT%H:%M:%SZ"),
    total_amount=str(invoice.total),
    tax_amount=str(invoice.tax),
    invoice_hash=signed_invoice["invoice_hash"],
    digital_signature=signed_invoice["digital_signature"],
    public_key=signed_invoice["public_key"],
    certificate_signature=signed_invoice["certificate_signature"],
)
```

The 9 tags in a Phase 2 QR:

| Tag | Field | Source |
|-----|-------|--------|
| 1 | Seller Name | Config |
| 2 | VAT Number | Config |
| 3 | Timestamp | Invoice date |
| 4 | Invoice Total | Invoice |
| 5 | Total VAT | Invoice |
| 6 | Invoice Hash | SHA-256 of signed XML |
| 7 | Digital Signature | ECDSA signature |
| 8 | Public Key | EC certificate |
| 9 | Certificate Signature | ZATCA certificate |

### Method 2: Using QRCodeService Directly

For PDF generation or custom output:

```python
from django_zatca.services.qr_code import QRCodeService, generate_phase1_qr
import base64

qr_data = generate_phase1_qr(...)
service = QRCodeService()

# Get SVG string (for embedding in HTML templates)
svg = service.render_html_svg(qr_data, size=200)

# Get base64-encoded image
b64 = service.render_as_base64(qr_data, size=200)

# Get data URI (for <img> tags)
uri = service.render_as_data_uri(qr_data, size=200)

# Save to file
service.render_to_file(qr_data, "/path/to/qr.svg", size=200)
```

**How it works:** `render()` auto-detects installed packages in this order:
1. `segno` → SVG (ZATCA-compatible, recommended)
2. `qrcode` + `SvgImage` → SVG (ZATCA-compatible)
3. `qrcode` + `Pillow` → PNG (ZATCA-compatible)
4. Built-in `SvgQrGenerator` → SVG (visual-only, **not ZATCA-compatible**)

---

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

---

## Management Commands

| Command | Required | Description |
|---------|----------|-------------|
| `python manage.py zatca_onboard` | **Phase 2** | Interactive onboarding wizard |
| `python manage.py zatca_check` | **Phase 1 & 2** | Check package readiness |
| `python manage.py zatca_sync` | Optional | Sync invoices to ZATCA |

---

## Signals

```python
from django_zatca.signals import invoice_cleared, invoice_reported, invoice_failed

@receiver(invoice_cleared)
def on_invoice_cleared(sender, invoice_data, result, **kwargs):
    # update your local db status
    pass
```

---

## Testing

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest
```

---

## Support

- **Issues**: [github.com/aghfatehi/django-zatca/issues](https://github.com/aghfatehi/django-zatca/issues)
- **Source**: [github.com/aghfatehi/django-zatca](https://github.com/aghfatehi/django-zatca)
- **ZATCA Portal**: [sandbox.zatca.gov.sa](https://sandbox.zatca.gov.sa)
