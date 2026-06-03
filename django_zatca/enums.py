from enum import Enum


class ZatcaPhase(str, Enum):
    PHASE1 = "phase_1"
    PHASE2 = "phase_2"
    BOTH = "both"


class Environment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

    def is_production(self):
        return self == self.PRODUCTION

    def is_sandbox(self):
        return self == self.SANDBOX


class InvoiceType(str, Enum):
    INVOICE = "INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    DEBIT_NOTE = "DEBIT_NOTE"

    def ubl_code(self):
        return {self.INVOICE: 388, self.CREDIT_NOTE: 381, self.DEBIT_NOTE: 383}.get(self, 388)

    def ubl_name(self):
        return {self.INVOICE: "0100000", self.CREDIT_NOTE: "0110000", self.DEBIT_NOTE: "0111000"}.get(self, "0100000")


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    REPORTED = "reported"
    CLEARED = "cleared"
    FAILED = "failed"
    COMPLIANCE_PASSED = "compliance_passed"
    COMPLIANCE_FAILED = "compliance_failed"


class Currency(str, Enum):
    SAR = "SAR"


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
