class ZatcaException(Exception):
    def __init__(self, message="ZATCA integration error", code=0, context=None):
        super().__init__(message)
        self.code = code
        self.context = context


class CertificateException(ZatcaException):
    pass


class ComplianceException(ZatcaException):
    pass
