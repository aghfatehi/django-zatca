import logging
from ..dto import InvoiceDTO, ComplianceResultDTO
from ..enums import Environment
from ..exceptions import CertificateException, ComplianceException
from .api_client import ApiClient
from . import certificate as cert_mod

logger = logging.getLogger("django_zatca")


class Phase2Service:
    def __init__(self, api_client=None, certificate_service=None, invoice_signer=None):
        self.api_client = api_client or ApiClient()
        self.cert_service = certificate_service or cert_mod
        self.invoice_signer = invoice_signer
        from .invoice_signer import InvoiceSignerService
        if self.invoice_signer is None:
            self.invoice_signer = InvoiceSignerService()

    def generate_keys_and_csr(self, egs_unit, solution_name="ERP"):
        from ..enums import Environment as Env

        logger.info("Phase2: Generating keys and CSR")
        private_key = self.cert_service.generate_ec_key_pair()
        csr = self.cert_service.generate_csr(
            private_key=private_key,
            solution_name=solution_name,
            egs_serial_number=egs_unit.get("uuid", ""),
            vat_number=egs_unit.get("vat_number", ""),
            branch_location=f'{egs_unit.get("location", {}).get("building", "")} {egs_unit.get("location", {}).get("street", "")}',
            branch_industry=egs_unit.get("branch_industry", ""),
            branch_name=egs_unit.get("branch_name", ""),
            taxpayer_name=egs_unit.get("vat_name", ""),
            taxpayer_provided_id=egs_unit.get("custom_id", egs_unit.get("uuid", "")),
            production=False,
        )

        return {
            "private_key": private_key,
            "csr": csr,
        }

    def issue_compliance_certificate(self, csr, otp):
        import base64
        logger.info("Phase2: Issuing compliance certificate")
        try:
            response = self.api_client.post("/compliance", {"csr": base64.b64encode(csr.encode("utf-8")).decode("ascii")}, otp=otp)
            issued = base64.b64decode(response["binarySecurityToken"]).decode("utf-8")
            response["binarySecurityToken"] = f"-----BEGIN CERTIFICATE-----\n{issued}\n-----END CERTIFICATE-----"
            return ComplianceResultDTO.from_api_response(response)
        except Exception as e:
            logger.error(f"Phase2: Compliance certificate failed: {e}")
            raise CertificateException(f"Failed to issue compliance certificate: {e}")

    def sign_invoice(self, invoice, egs_unit, certificate, private_key):
        logger.info(f"Phase2: Signing invoice {invoice.invoice_serial_number}")
        return self.invoice_signer.sign(invoice, egs_unit, certificate, private_key)

    def check_compliance(self, signed_invoice_xml, invoice_hash, certificate, secret):
        logger.info("Phase2: Checking invoice compliance")
        try:
            import base64
            import xml.etree.ElementTree as ET
            root = ET.fromstring(signed_invoice_xml)
            ns = {"ns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
            uuid_el = root.find(".//ns:UUID", ns)
            uuid = uuid_el.text if uuid_el is not None else ""
            response = self.api_client.post("/compliance/invoices", {
                "invoiceHash": invoice_hash,
                "uuid": uuid,
                "invoice": base64.b64encode(signed_invoice_xml.encode("utf-8")).decode("ascii"),
            }, certificate=certificate, secret=secret)
            return ComplianceResultDTO.from_api_response(response)
        except Exception as e:
            logger.error(f"Phase2: Compliance check failed: {e}")
            raise ComplianceException(f"Invoice compliance check failed: {e}")

    def clear_invoice(self, signed_invoice_xml, invoice_hash, certificate, secret):
        logger.info("Phase2: Clearing invoice")
        try:
            import base64
            import xml.etree.ElementTree as ET
            root = ET.fromstring(signed_invoice_xml)
            ns = {"ns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
            uuid_el = root.find(".//ns:UUID", ns)
            uuid = uuid_el.text if uuid_el is not None else ""
            response = self.api_client.post("/invoices/clearance", {
                "invoiceHash": invoice_hash,
                "uuid": uuid,
                "invoice": base64.b64encode(signed_invoice_xml.encode("utf-8")).decode("ascii"),
            }, certificate=certificate, secret=secret)
            return ComplianceResultDTO.from_api_response(response)
        except Exception as e:
            logger.error(f"Phase2: Clearance failed: {e}")
            raise ComplianceException(f"Invoice clearance failed: {e}")

    def report_invoice(self, signed_invoice_xml, invoice_hash, certificate, secret):
        logger.info("Phase2: Reporting invoice")
        try:
            import base64
            import xml.etree.ElementTree as ET
            root = ET.fromstring(signed_invoice_xml)
            ns = {"ns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"}
            uuid_el = root.find(".//ns:UUID", ns)
            uuid = uuid_el.text if uuid_el is not None else ""
            response = self.api_client.post("/invoices/reporting", {
                "invoiceHash": invoice_hash,
                "uuid": uuid,
                "invoice": base64.b64encode(signed_invoice_xml.encode("utf-8")).decode("ascii"),
            }, certificate=certificate, secret=secret)
            return ComplianceResultDTO.from_api_response(response)
        except Exception as e:
            logger.error(f"Phase2: Reporting failed: {e}")
            raise ComplianceException(f"Invoice reporting failed: {e}")

    def submit_invoice(self, signed_invoice_xml, invoice_hash, certificate, secret):
        from ..enums import Environment as Env
        env = Env(self.api_client.environment)
        if env.is_sandbox():
            return self.check_compliance(signed_invoice_xml, invoice_hash, certificate, secret)
        clearance = self.clear_invoice(signed_invoice_xml, invoice_hash, certificate, secret)
        if not clearance.success:
            return self.report_invoice(signed_invoice_xml, invoice_hash, certificate, secret)
        return clearance
