from django.conf import settings


def get_setting(name, default=None):
    return getattr(settings, name, default)


DEFAULTS = {
    "ZATCA_PHASE": "both",
    "ZATCA_ENVIRONMENT": "sandbox",
    "ZATCA_API_SANDBOX_BASE": "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal",
    "ZATCA_API_PRODUCTION_BASE": "https://gw-fatoora.zatca.gov.sa/e-invoicing",
    "ZATCA_API_VERSION": "V2",
    "ZATCA_API_TIMEOUT": 60,
    "ZATCA_API_MIDDLEWARE": "api",
    "ZATCA_EGS_UUID": "",
    "ZATCA_VAT_NUMBER": "",
    "ZATCA_VAT_NAME": "",
    "ZATCA_CRN_NUMBER": "",
    "ZATCA_INDUSTRY": "Retail",
    "ZATCA_CITY": "Riyadh",
    "ZATCA_CITY_SUBDIVISION": "",
    "ZATCA_STREET": "",
    "ZATCA_BUILDING": "0000",
    "ZATCA_PLOT_ID": "0000",
    "ZATCA_POSTAL_ZONE": "00000",
    "ZATCA_BRANCH_NAME": "Main Branch",
    "ZATCA_CERTIFICATE": "",
    "ZATCA_PRIVATE_KEY": "",
    "ZATCA_SECRET": "",
    "ZATCA_QUEUE_CONNECTION": "sync",
    "ZATCA_QUEUE_NAME": "zatca",
    "ZATCA_QUEUE_TRIES": 3,
    "ZATCA_QUEUE_TIMEOUT": 120,
    "ZATCA_RETRY_DELAY_MINUTES": 60,
    "ZATCA_LOGGING_ENABLED": True,
    "ZATCA_LOG_LEVEL": "info",
    "ZATCA_LOG_MASK_PII": True,
    "ZATCA_QR_SIZE": 200,
    "ZATCA_QR_RENDERER": "svg",
}


def zatca_setting(name, default=None):
    key = f"ZATCA_{name}"
    if hasattr(settings, key):
        return getattr(settings, key)
    env_val = DEFAULTS.get(key)
    if env_val is not None:
        return env_val
    return default


def get_egs_config():
    return {
        "uuid": zatca_setting("EGS_UUID", ""),
        "vat_number": zatca_setting("VAT_NUMBER", ""),
        "vat_name": zatca_setting("VAT_NAME", ""),
        "crn_number": zatca_setting("CRN_NUMBER", ""),
        "branch_industry": zatca_setting("INDUSTRY", "Retail"),
        "branch_name": zatca_setting("BRANCH_NAME", "Main Branch"),
        "location": {
            "city": zatca_setting("CITY", "Riyadh"),
            "city_subdivision": zatca_setting("CITY_SUBDIVISION", ""),
            "street": zatca_setting("STREET", ""),
            "building": zatca_setting("BUILDING", "0000"),
            "plot_identification": zatca_setting("PLOT_ID", "0000"),
            "postal_zone": zatca_setting("POSTAL_ZONE", "00000"),
        },
    }
