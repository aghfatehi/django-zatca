import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "test-insecure-not-used-in-prod"
DEBUG = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_zatca",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

ZATCA = {
    "PHASE": "both",
    "ENVIRONMENT": "sandbox",
    "EGS_UUID": "test-egs-uuid",
    "VAT_NUMBER": "311111111100003",
    "VAT_NAME": "Test Company",
    "CITY": "Riyadh",
    "CITY_SUBDIVISION": "Riyadh",
    "STREET": "Olaya",
    "BUILDING": "1234",
    "PLOT_IDENTIFICATION": "5678",
    "POSTAL_ZONE": "12345",
    "BRANCH_NAME": "Main Branch",
    "BRANCH_INDUSTRY": "Retail",
    "CRN_NUMBER": "CRN123",
    "API_SANDBOX_BASE": "https://sandbox.zatca.example.com",
    "API_PRODUCTION_BASE": "https://api.my.example.com",
}
