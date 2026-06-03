from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class LineItemDTO:
    id: str = "1"
    name: str = ""
    quantity: float = 1.0
    tax_exclusive_price: float = 0.0
    vat_percent: float = 0.15
    other_taxes: list = field(default_factory=list)
    discounts: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=str(data.get("id", "1")),
            name=data.get("name", ""),
            quantity=float(data.get("quantity", 1)),
            tax_exclusive_price=float(data.get("tax_exclusive_price", 0)),
            vat_percent=float(data.get("vat_percent", 0.15)),
            other_taxes=data.get("other_taxes", []),
            discounts=data.get("discounts", []),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InvoiceDTO:
    invoice_serial_number: str = ""
    invoice_counter_number: int = 1
    issue_date: str = ""
    issue_time: str = ""
    currency: str = "SAR"
    previous_invoice_hash: str = ""
    invoice_type: str = "INVOICE"
    customer_name: Optional[str] = None
    customer_vat_number: Optional[str] = None
    line_items: list = field(default_factory=list)

    def __post_init__(self):
        from datetime import date, datetime
        if not self.issue_date:
            self.issue_date = date.today().isoformat()
        if not self.issue_time:
            self.issue_time = datetime.now().strftime("%H:%M:%S")

    @classmethod
    def from_dict(cls, data: dict):
        items = []
        for li in data.get("line_items", []):
            if isinstance(li, dict):
                items.append(LineItemDTO.from_dict(li))
            else:
                items.append(li)
        return cls(
            invoice_serial_number=data.get("invoice_serial_number", ""),
            invoice_counter_number=data.get("invoice_counter_number", 1),
            issue_date=data.get("issue_date", ""),
            issue_time=data.get("issue_time", ""),
            currency=data.get("currency", "SAR"),
            previous_invoice_hash=data.get("previous_invoice_hash", ""),
            invoice_type=data.get("invoice_type", "INVOICE"),
            customer_name=data.get("customer_name"),
            customer_vat_number=data.get("customer_vat_number"),
            line_items=items,
        )

    def to_dict(self) -> dict:
        items = []
        for li in self.line_items:
            if isinstance(li, LineItemDTO):
                items.append(li.to_dict())
            else:
                items.append(li)
        return {
            "invoice_serial_number": self.invoice_serial_number,
            "invoice_counter_number": self.invoice_counter_number,
            "issue_date": self.issue_date,
            "issue_time": self.issue_time,
            "currency": self.currency,
            "previous_invoice_hash": self.previous_invoice_hash,
            "invoice_type": self.invoice_type,
            "customer_name": self.customer_name,
            "customer_vat_number": self.customer_vat_number,
            "line_items": items,
        }


@dataclass
class EgsUnitDTO:
    uuid: str = ""
    custom_id: str = ""
    model: str = "Desktop"
    vat_number: str = ""
    vat_name: str = ""
    crn_number: str = ""
    city: str = ""
    city_subdivision: str = ""
    street: str = ""
    building: str = "0000"
    plot_identification: str = "0000"
    postal_zone: str = "00000"
    branch_name: str = ""
    branch_industry: str = ""

    @classmethod
    def from_dict(cls, data: dict):
        loc = data.get("location", {})
        return cls(
            uuid=data.get("uuid", ""),
            custom_id=data.get("custom_id", ""),
            model=data.get("model", "Desktop"),
            vat_number=data.get("vat_number", ""),
            vat_name=data.get("vat_name", ""),
            crn_number=data.get("crn_number", ""),
            city=loc.get("city", data.get("city", "")),
            city_subdivision=loc.get("city_subdivision", data.get("city_subdivision", "")),
            street=loc.get("street", data.get("street", "")),
            building=loc.get("building", data.get("building", "0000")),
            plot_identification=loc.get("plot_identification", data.get("plot_identification", "0000")),
            postal_zone=loc.get("postal_zone", data.get("postal_zone", "00000")),
            branch_name=data.get("branch_name", ""),
            branch_industry=data.get("branch_industry", ""),
        )

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "custom_id": self.custom_id,
            "model": self.model,
            "vat_number": self.vat_number,
            "vat_name": self.vat_name,
            "crn_number": self.crn_number,
            "location": {
                "city": self.city,
                "city_subdivision": self.city_subdivision,
                "street": self.street,
                "building": self.building,
                "plot_identification": self.plot_identification,
                "postal_zone": self.postal_zone,
            },
            "branch_name": self.branch_name,
            "branch_industry": self.branch_industry,
        }


@dataclass
class ComplianceResultDTO:
    success: bool = False
    request_id: str = ""
    binary_security_token: str = ""
    secret: str = ""
    error_message: Optional[str] = None
    validation_results: Optional[dict] = None

    @classmethod
    def from_api_response(cls, response: dict):
        has_error = "errors" in response or "binarySecurityToken" not in response
        return cls(
            success=not has_error,
            request_id=response.get("requestID", ""),
            binary_security_token=response.get("binarySecurityToken", ""),
            secret=response.get("secret", ""),
            error_message=response.get("errors", [{}])[0].get("message") if response.get("errors") else None,
            validation_results=response.get("validationResults"),
        )

    @classmethod
    def failed(cls, message: str):
        return cls(success=False, error_message=message)
