from django.urls import path
from . import views

urlpatterns = [
    path("zatca/status", views.zatca_status, name="zatca-status"),
    path("zatca/onboard", views.zatca_onboard, name="zatca-onboard"),
    path("zatca/invoice/sync", views.zatca_sync_invoice, name="zatca-sync-invoice"),
]
