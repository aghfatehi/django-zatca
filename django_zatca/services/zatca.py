import logging
from ..enums import ZatcaPhase, Environment
from ..defaults import zatca_setting
from ..dto import InvoiceDTO

logger = logging.getLogger("django_zatca")


class ZatcaService:
    def __init__(self, phase1=None, phase2=None, qr_service=None):
        self.active_phase = ZatcaPhase(zatca_setting("PHASE", "both"))
        self.environment = Environment(zatca_setting("ENVIRONMENT", "sandbox"))

        from .phase1 import Phase1Service
        from .phase2 import Phase2Service
        from .qr_code import QRCodeService

        self._phase1 = phase1 or Phase1Service(qr_service=qr_service)
        self._phase2 = phase2 or Phase2Service()
        self._qr = qr_service or QRCodeService()

    @property
    def phase(self):
        return self.active_phase

    @property
    def env(self):
        return self.environment

    def is_phase1_enabled(self):
        return self.active_phase in (ZatcaPhase.PHASE1, ZatcaPhase.BOTH)

    def is_phase2_enabled(self):
        return self.active_phase in (ZatcaPhase.PHASE2, ZatcaPhase.BOTH)

    def phase1(self):
        return self._phase1

    def phase2(self):
        return self._phase2

    def qr(self):
        return self._qr

    def generate_invoice_qr(self, invoice, egs_unit):
        if self.is_phase1_enabled():
            return self._phase1.generate_qr_code_from_invoice(invoice, egs_unit)
        if self.is_phase2_enabled():
            logger.warning("Phase 2 QR requires signed invoice. Use phase2().sign_invoice() instead.")
        return self._phase1.generate_qr_code_from_invoice(invoice, egs_unit)

    def generate_phase2_qr(self, seller_name, vat_number, invoice_date,
                           total_amount, tax_amount, invoice_hash,
                           digital_signature, public_key, certificate_signature):
        from .qr_code import generate_phase2_qr as _gen_p2
        return _gen_p2(
            seller_name=seller_name,
            vat_number=vat_number,
            invoice_date=invoice_date,
            total_amount=total_amount,
            tax_amount=tax_amount,
            invoice_hash=invoice_hash,
            digital_signature=digital_signature,
            public_key=public_key,
            certificate_signature=certificate_signature,
        )
