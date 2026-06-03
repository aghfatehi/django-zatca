import logging
from xml.dom import minidom
from datetime import datetime
from ..dto import InvoiceDTO
from ..enums import InvoiceType

logger = logging.getLogger("django_zatca")


class InvoiceSignerService:
    def __init__(self, qr_service=None, certificate_service=None):
        from .qr_code import QRCodeService
        from . import certificate as cert_mod
        self.qr_service = qr_service or QRCodeService()
        self.cert_service = certificate_service or cert_mod

    def sign(self, invoice, egs_unit, certificate, private_key):
        from . import certificate as cert_mod
        logger.info(f"Starting invoice signing process: {invoice.invoice_serial_number}")

        invoice_xml = self._build_xml(invoice, egs_unit)
        invoice_hash = self._compute_invoice_hash(invoice_xml)
        cert_info = cert_mod.parse_certificate_info(certificate)
        digital_signature = self._create_digital_signature(invoice_hash, private_key)

        invoice_date = f"{invoice.issue_date}T{invoice.issue_time}Z"
        from .qr_code import generate_phase2_qr
        qr_data = generate_phase2_qr(
            seller_name=egs_unit.get("vat_name", ""),
            vat_number=egs_unit.get("vat_number", ""),
            invoice_date=invoice_date,
            total_amount=self._get_total_amount(invoice_xml),
            tax_amount=self._get_tax_amount(invoice_xml),
            invoice_hash=invoice_hash,
            digital_signature=digital_signature,
            public_key=cert_info["public_key"],
            certificate_signature=cert_info["signature"],
        )

        signed_xml = self._embed_signatures(
            invoice_xml=invoice_xml,
            invoice_hash=invoice_hash,
            digital_signature=digital_signature,
            certificate=certificate,
            cert_info=cert_info,
            qr_data=qr_data,
        )

        logger.info(f"Invoice signed successfully: {invoice.invoice_serial_number}")

        return {
            "signed_xml": signed_xml,
            "invoice_hash": invoice_hash,
            "qr_tlv": qr_data,
            "public_key": cert_info["public_key"],
        }

    def _build_xml(self, invoice, egs_unit):
        impl = minidom.getDOMImplementation()
        doc = impl.createDocument(None, "Invoice", None)
        root = doc.documentElement

        ns = {
            "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "xmlns:ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        }
        for k, v in ns.items():
            root.setAttribute(k, v)

        self._add_elem(doc, root, "cbc:ProfileID", "reporting:1.0")
        self._add_elem(doc, root, "cbc:ID", invoice.invoice_serial_number)
        self._add_elem(doc, root, "cbc:UUID", egs_unit.get("uuid", ""))
        self._add_elem(doc, root, "cbc:IssueDate", invoice.issue_date)
        self._add_elem(doc, root, "cbc:IssueTime", invoice.issue_time)

        inv_type = InvoiceType(invoice.invoice_type) if invoice.invoice_type in InvoiceType._value2member_map_ else InvoiceType.INVOICE
        tc = doc.createElement("cbc:InvoiceTypeCode")
        tc.setAttribute("name", inv_type.ubl_name())
        tc.appendChild(doc.createTextNode(str(inv_type.ubl_code())))
        root.appendChild(tc)

        self._add_elem(doc, root, "cbc:DocumentCurrencyCode", invoice.currency)
        self._add_elem(doc, root, "cbc:TaxCurrencyCode", invoice.currency)

        self._add_additional_doc_ref(doc, root, "ICV", str(invoice.invoice_counter_number))

        if invoice.previous_invoice_hash:
            pih = self._add_additional_doc_ref(doc, root, "PIH")
            att = doc.createElement("cac:Attachment")
            bo = doc.createElement("cbc:EmbeddedDocumentBinaryObject")
            bo.setAttribute("mimeCode", "text/plain")
            bo.appendChild(doc.createTextNode(invoice.previous_invoice_hash))
            att.appendChild(bo)
            pih.appendChild(att)

        self._add_additional_doc_ref(doc, root, "QR")

        sig = doc.createElement("cac:Signature")
        self._add_elem(doc, sig, "cbc:ID", "urn:oasis:names:specification:ubl:signature:Invoice")
        self._add_elem(doc, sig, "cbc:SignatureMethod", "urn:oasis:names:specification:ubl:dsig:enveloped:xades")
        root.appendChild(sig)

        self._append_supplier_party(doc, root, egs_unit)
        self._append_customer_party(doc, root, invoice, egs_unit)

        delivery = doc.createElement("cac:Delivery")
        self._add_elem(doc, delivery, "cbc:ActualDeliveryDate", invoice.issue_date)
        root.appendChild(delivery)

        payment = doc.createElement("cac:PaymentMeans")
        self._add_elem(doc, payment, "cbc:PaymentMeansCode", "10")
        root.appendChild(payment)

        self._append_line_items(doc, root, invoice)
        self._append_tax_totals(doc, root, invoice)
        self._append_legal_monetary_total(doc, root, invoice)

        root.insertBefore(doc.createComment(" UBLExtensions "), root.firstChild)
        return doc

    def _compute_invoice_hash(self, doc):
        import hashlib, base64, copy
        clone = copy.deepcopy(doc)

        for tag_name in ["UBLExtensions", "Signature"]:
            for el in clone.getElementsByTagName(tag_name):
                if el.parentNode:
                    el.parentNode.removeChild(el)

        qr_refs = clone.getElementsByTagName("AdditionalDocumentReference")
        for ref in list(qr_refs):
            ids = ref.getElementsByTagName("ID")
            if ids and ids[0].firstChild and ids[0].firstChild.nodeValue == "QR":
                ref.parentNode.removeChild(ref)

        pure = clone.toxml()
        pure = pure.replace('<?xml version="1.0" ?>', '')
        pure = pure.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
        pure = pure.replace("<cac:AccountingCustomerParty/>", "<cac:AccountingCustomerParty></cac:AccountingCustomerParty>")
        pure = pure.strip()

        h = hashlib.sha256(pure.encode("utf-8")).digest()
        return base64.b64encode(h).decode("ascii")

    def _create_digital_signature(self, invoice_hash, private_key):
        import base64, hashlib
        from .certificate import clean_private_key

        clean_key = clean_private_key(private_key)
        wrapped = f"-----BEGIN EC PRIVATE KEY-----\n{clean_key}\n-----END EC PRIVATE KEY-----"

        import tempfile, subprocess, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as kf:
            kf.write(wrapped)
            kpath = kf.name
        try:
            hash_b64 = base64.b64encode(hashlib.sha256(invoice_hash.encode("utf-8")).digest()).decode("ascii")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as hf:
                hf.write(hash_b64)
                hpath = hf.name
            try:
                sig_result = subprocess.check_output(
                    ["openssl", "dgst", "-sha256", "-sign", kpath, hpath],
                    stderr=subprocess.STDOUT,
                )
                return base64.b64encode(sig_result).decode("ascii")
            finally:
                os.remove(hpath)
        finally:
            os.remove(kpath)

    def _embed_signatures(self, invoice_xml, invoice_hash, digital_signature,
                          certificate, cert_info, qr_data):
        sign_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        signed_props_for_signing = (
            f'<xades:SignedProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Id="xadesSignedProperties">'
            f'<xades:SignedSignatureProperties>'
            f'<xades:SigningTime>{sign_ts}</xades:SigningTime>'
            f'<xades:SigningCertificate>'
            f'<xades:Cert>'
            f'<xades:CertDigest>'
            f'<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>'
            f'<ds:DigestValue>{cert_info["hash"]}</ds:DigestValue>'
            f'</xades:CertDigest>'
            f'<xades:IssuerSerial>'
            f'<ds:X509IssuerName>{cert_info["issuer"]}</ds:X509IssuerName>'
            f'<ds:X509SerialNumber>{cert_info["serial_number"]}</ds:X509SerialNumber>'
            f'</xades:IssuerSerial>'
            f'</xades:Cert>'
            f'</xades:SigningCertificate>'
            f'</xades:SignedSignatureProperties>'
            f'</xades:SignedProperties>'
        )

        import hashlib, base64
        signed_hash = base64.b64encode(
            hashlib.sha256(signed_props_for_signing.encode("utf-8")).digest()
        ).decode("ascii")

        signed_props_xml = signed_props_for_signing

        clean_cert = certificate.replace("-----BEGIN CERTIFICATE-----", "")
        clean_cert = clean_cert.replace("-----END CERTIFICATE-----", "").strip()

        ubl_ext = (
            f'<ext:UBLExtensions>'
            f'<ext:UBLExtension>'
            f'<ext:ExtensionURI>urn:oasis:names:specification:ubl:dsig:enveloped:xades</ext:ExtensionURI>'
            f'<ext:ExtensionContent>'
            f'<sig:UBLDocumentSignatures xmlns:sac="urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2" '
            f'xmlns:sbc="urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2" '
            f'xmlns:sig="urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2">'
            f'<sac:SignatureInformation>'
            f'<cbc:ID>urn:oasis:names:specification:ubl:signature:1</cbc:ID>'
            f'<sbc:ReferencedSignatureID>urn:oasis:names:specification:ubl:signature:Invoice</sbc:ReferencedSignatureID>'
            f'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="signature">'
            f'<ds:SignedInfo>'
            f'<ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>'
            f'<ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"/>'
            f'<ds:Reference Id="invoiceSignedData" URI="">'
            f'<ds:Transforms>'
            f'<ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116"><ds:XPath>not(//ancestor-or-self::ext:UBLExtensions)</ds:XPath></ds:Transform>'
            f'<ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116"><ds:XPath>not(//ancestor-or-self::cac:Signature)</ds:XPath></ds:Transform>'
            f'<ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116"><ds:XPath>not(//ancestor-or-self::cac:AdditionalDocumentReference[cbc:ID=\'QR\'])</ds:XPath></ds:Transform>'
            f'<ds:Transform Algorithm="http://www.w3.org/2006/12/xml-c14n11"/>'
            f'</ds:Transforms>'
            f'<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>'
            f'<ds:DigestValue>{invoice_hash}</ds:DigestValue>'
            f'</ds:Reference>'
            f'<ds:Reference Type="http://www.w3.org/2000/09/xmldsig#SignatureProperties" URI="#xadesSignedProperties">'
            f'<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>'
            f'<ds:DigestValue>{signed_hash}</ds:DigestValue>'
            f'</ds:Reference>'
            f'</ds:SignedInfo>'
            f'<ds:SignatureValue>{digital_signature}</ds:SignatureValue>'
            f'<ds:KeyInfo>'
            f'<ds:X509Data>'
            f'<ds:X509Certificate>{clean_cert}</ds:X509Certificate>'
            f'</ds:X509Data>'
            f'</ds:KeyInfo>'
            f'<ds:Object>'
            f'<xades:QualifyingProperties Target="signature" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">'
            f'{signed_props_xml}'
            f'</xades:QualifyingProperties>'
            f'</ds:Object>'
            f'</ds:Signature>'
            f'</sac:SignatureInformation>'
            f'</sig:UBLDocumentSignatures>'
            f'</ext:ExtensionContent>'
            f'</ext:UBLExtension>'
            f'</ext:UBLExtensions>'
        )

        xml_str = invoice_xml.toxml()
        xml_str = xml_str.replace("<!-- UBLExtensions -->", ubl_ext)
        xml_str = xml_str.replace(
            '<cac:AdditionalDocumentReference><cbc:ID>QR</cbc:ID></cac:AdditionalDocumentReference>',
            f'<cac:AdditionalDocumentReference><cbc:ID>QR</cbc:ID><cac:Attachment><cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">{qr_data}</cbc:EmbeddedDocumentBinaryObject></cac:Attachment></cac:AdditionalDocumentReference>',
        )

        return xml_str

    def _append_supplier_party(self, doc, root, egs_unit):
        supplier = doc.createElement("cac:AccountingSupplierParty")
        party = doc.createElement("cac:Party")

        pid = doc.createElement("cac:PartyIdentification")
        self._add_elem(doc, pid, "cbc:ID", egs_unit.get("crn_number", ""))
        pid.firstChild.setAttribute("schemeID", "CRN")
        party.appendChild(pid)

        address = doc.createElement("cac:PostalAddress")
        loc = egs_unit.get("location", {})
        self._add_elem(doc, address, "cbc:StreetName", loc.get("street", ""))
        self._add_elem(doc, address, "cbc:BuildingNumber", loc.get("building", "0000"))
        self._add_elem(doc, address, "cbc:PlotIdentification", loc.get("plot_identification", "0000"))
        self._add_elem(doc, address, "cbc:CitySubdivisionName", loc.get("city_subdivision", ""))
        self._add_elem(doc, address, "cbc:CityName", loc.get("city", ""))
        self._add_elem(doc, address, "cbc:PostalZone", loc.get("postal_zone", ""))
        country = doc.createElement("cac:Country")
        self._add_elem(doc, country, "cbc:IdentificationCode", "SA")
        address.appendChild(country)
        party.appendChild(address)

        tax_scheme = doc.createElement("cac:PartyTaxScheme")
        self._add_elem(doc, tax_scheme, "cbc:CompanyID", egs_unit.get("vat_number", ""))
        ts = doc.createElement("cac:TaxScheme")
        self._add_elem(doc, ts, "cbc:ID", "VAT")
        tax_scheme.appendChild(ts)
        party.appendChild(tax_scheme)

        legal = doc.createElement("cac:PartyLegalEntity")
        self._add_elem(doc, legal, "cbc:RegistrationName", egs_unit.get("vat_name", ""))
        party.appendChild(legal)

        supplier.appendChild(party)
        root.appendChild(supplier)

    def _append_customer_party(self, doc, root, invoice, egs_unit):
        customer = doc.createElement("cac:AccountingCustomerParty")
        party = doc.createElement("cac:Party")

        if invoice.customer_vat_number:
            pid = doc.createElement("cac:PartyIdentification")
            self._add_elem(doc, pid, "cbc:ID", invoice.customer_vat_number)
            pid.firstChild.setAttribute("schemeID", "NAT")
            party.appendChild(pid)

        address = doc.createElement("cac:PostalAddress")
        loc = egs_unit.get("location", {})
        self._add_elem(doc, address, "cbc:StreetName", loc.get("street", ""))
        self._add_elem(doc, address, "cbc:BuildingNumber", loc.get("building", "0000"))
        self._add_elem(doc, address, "cbc:CitySubdivisionName", loc.get("city_subdivision", ""))
        self._add_elem(doc, address, "cbc:CityName", loc.get("city", ""))
        self._add_elem(doc, address, "cbc:PostalZone", loc.get("postal_zone", ""))
        country = doc.createElement("cac:Country")
        self._add_elem(doc, country, "cbc:IdentificationCode", "SA")
        address.appendChild(country)
        party.appendChild(address)

        if invoice.customer_name:
            legal = doc.createElement("cac:PartyLegalEntity")
            self._add_elem(doc, legal, "cbc:RegistrationName", invoice.customer_name)
            party.appendChild(legal)

        customer.appendChild(party)
        root.appendChild(customer)

    def _append_line_items(self, doc, root, invoice):
        for item in invoice.line_items:
            if isinstance(item, dict):
                li = item
            else:
                li = item.to_dict() if hasattr(item, "to_dict") else item
            line = doc.createElement("cac:InvoiceLine")
            self._add_elem(doc, line, "cbc:ID", str(li.get("id", "")))

            qty = doc.createElement("cbc:InvoicedQuantity")
            qty.setAttribute("unitCode", "PCE")
            qty.appendChild(doc.createTextNode(str(li.get("quantity", 0))))
            line.appendChild(qty)

            subtotal = float(li.get("tax_exclusive_price", 0)) * float(li.get("quantity", 0))
            discounts_total = sum(float(d.get("amount", 0)) for d in li.get("discounts", []))
            taxable = subtotal - discounts_total
            vat = taxable * float(li.get("vat_percent", 0))

            self._add_elem(doc, line, "cbc:LineExtensionAmount", f"{taxable:.2f}",
                          {"currencyID": "SAR"})

            tax_total = doc.createElement("cac:TaxTotal")
            self._add_elem(doc, tax_total, "cbc:TaxAmount", f"{vat:.2f}", {"currencyID": "SAR"})
            self._add_elem(doc, tax_total, "cbc:RoundingAmount", f"{taxable + vat:.2f}", {"currencyID": "SAR"})
            line.appendChild(tax_total)

            item_el = doc.createElement("cac:Item")
            self._add_elem(doc, item_el, "cbc:Name", li.get("name", ""))

            cat = doc.createElement("cac:ClassifiedTaxCategory")
            vat_pct = float(li.get("vat_percent", 0)) * 100
            self._add_elem(doc, cat, "cbc:ID", "S" if vat_pct > 0 else "O")
            self._add_elem(doc, cat, "cbc:Percent", f"{vat_pct:.2f}")
            ts2 = doc.createElement("cac:TaxScheme")
            self._add_elem(doc, ts2, "cbc:ID", "VAT")
            cat.appendChild(ts2)
            item_el.appendChild(cat)
            line.appendChild(item_el)

            price = doc.createElement("cac:Price")
            self._add_elem(doc, price, "cbc:PriceAmount", str(li.get("tax_exclusive_price", 0)),
                          {"currencyID": "SAR"})
            line.appendChild(price)

            root.appendChild(line)

    def _append_tax_totals(self, doc, root, invoice):
        total_vat = 0.0
        tax_subtotals = {}

        for item in invoice.line_items:
            if isinstance(item, dict):
                li = item
            else:
                li = item.to_dict() if hasattr(item, "to_dict") else item
            subtotal = float(li.get("tax_exclusive_price", 0)) * float(li.get("quantity", 0))
            discounts = sum(float(d.get("amount", 0)) for d in li.get("discounts", []))
            taxable = subtotal - discounts
            vat = taxable * float(li.get("vat_percent", 0))
            total_vat += vat

            pct = float(li.get("vat_percent", 0))
            key = str(pct)
            if key not in tax_subtotals:
                tax_subtotals[key] = {"taxable": 0, "vat": 0, "percent": pct}
            tax_subtotals[key]["taxable"] += taxable
            tax_subtotals[key]["vat"] += vat

        tt1 = doc.createElement("cac:TaxTotal")
        self._add_elem(doc, tt1, "cbc:TaxAmount", f"{total_vat:.2f}", {"currencyID": "SAR"})

        for sub in tax_subtotals.values():
            st = doc.createElement("cac:TaxSubtotal")
            self._add_elem(doc, st, "cbc:TaxableAmount", f"{sub['taxable']:.2f}", {"currencyID": "SAR"})
            self._add_elem(doc, st, "cbc:TaxAmount", f"{sub['vat']:.2f}", {"currencyID": "SAR"})
            cat = doc.createElement("cac:TaxCategory")
            id_el = doc.createElement("cbc:ID")
            id_el.setAttribute("schemeID", "UN/ECE 5305")
            id_el.setAttribute("schemeAgencyID", "6")
            id_el.appendChild(doc.createTextNode("S" if sub["percent"] > 0 else "O"))
            cat.appendChild(id_el)
            self._add_elem(doc, cat, "cbc:Percent", f"{sub['percent'] * 100:.2f}")
            ts = doc.createElement("cac:TaxScheme")
            ts_id = doc.createElement("cbc:ID")
            ts_id.setAttribute("schemeID", "UN/ECE 5153")
            ts_id.setAttribute("schemeAgencyID", "6")
            ts_id.appendChild(doc.createTextNode("VAT"))
            ts.appendChild(ts_id)
            cat.appendChild(ts)
            st.appendChild(cat)
            tt1.appendChild(st)
        root.appendChild(tt1)

        tt2 = doc.createElement("cac:TaxTotal")
        self._add_elem(doc, tt2, "cbc:TaxAmount", f"{total_vat:.2f}", {"currencyID": "SAR"})
        root.appendChild(tt2)

    def _append_legal_monetary_total(self, doc, root, invoice):
        total_subtotal = 0.0
        total_vat = 0.0

        for item in invoice.line_items:
            if isinstance(item, dict):
                li = item
            else:
                li = item.to_dict() if hasattr(item, "to_dict") else item
            subtotal = float(li.get("tax_exclusive_price", 0)) * float(li.get("quantity", 0))
            discounts = sum(float(d.get("amount", 0)) for d in li.get("discounts", []))
            taxable = subtotal - discounts
            total_subtotal += taxable
            total_vat += taxable * float(li.get("vat_percent", 0))

        total = doc.createElement("cac:LegalMonetaryTotal")
        self._add_elem(doc, total, "cbc:LineExtensionAmount", f"{total_subtotal:.2f}", {"currencyID": "SAR"})
        self._add_elem(doc, total, "cbc:TaxExclusiveAmount", f"{total_subtotal:.2f}", {"currencyID": "SAR"})
        self._add_elem(doc, total, "cbc:TaxInclusiveAmount", f"{total_subtotal + total_vat:.2f}", {"currencyID": "SAR"})
        self._add_elem(doc, total, "cbc:AllowanceTotalAmount", "0", {"currencyID": "SAR"})
        self._add_elem(doc, total, "cbc:PrepaidAmount", "0", {"currencyID": "SAR"})
        self._add_elem(doc, total, "cbc:PayableAmount", f"{total_subtotal + total_vat:.2f}", {"currencyID": "SAR"})
        root.appendChild(total)

    def _add_additional_doc_ref(self, doc, root, ref_id, uuid_val=None):
        ref = doc.createElement("cac:AdditionalDocumentReference")
        self._add_elem(doc, ref, "cbc:ID", ref_id)
        if uuid_val is not None:
            self._add_elem(doc, ref, "cbc:UUID", uuid_val)
        root.appendChild(ref)
        return ref

    def _add_elem(self, doc, parent, name, value="", attrs=None):
        el = doc.createElement(name)
        if value:
            el.appendChild(doc.createTextNode(str(value)))
        if attrs:
            for k, v in attrs.items():
                el.setAttribute(k, str(v))
        parent.appendChild(el)

    def _get_total_amount(self, doc):
        amounts = doc.getElementsByTagName("TaxInclusiveAmount")
        return amounts[0].firstChild.nodeValue if amounts and amounts[0].firstChild else "0"

    def _get_tax_amount(self, doc):
        totals = doc.getElementsByTagName("TaxTotal")
        if totals:
            amounts = totals[0].getElementsByTagName("TaxAmount")
            if amounts and amounts[0].firstChild:
                return amounts[0].firstChild.nodeValue
        return "0"
