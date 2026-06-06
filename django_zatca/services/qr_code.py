import base64
import struct


def generate_tlv(tags):
    tlv = b""
    for idx, value in enumerate(tags):
        tag = idx + 1
        value = str(value).encode("utf-8")
        length = len(value)
        tlv += struct.pack("B", tag)
        tlv += struct.pack("B", length)
        tlv += value
    return base64.b64encode(tlv).decode("ascii")


def generate_phase1_qr(seller_name, vat_number, invoice_date, total_amount, tax_amount):
    return generate_tlv([seller_name, vat_number, invoice_date, total_amount, tax_amount])


def generate_phase2_qr(seller_name, vat_number, invoice_date, total_amount, tax_amount,
                       invoice_hash, digital_signature, public_key, certificate_signature):
    return generate_tlv([
        seller_name, vat_number, invoice_date, total_amount, tax_amount,
        invoice_hash, digital_signature, public_key, certificate_signature,
    ])


class QRCodeService:
    def render(self, tlv_data, size=200):
        # Priority 1: segno (pure Python, no deps, reliable SVG)
        try:
            import segno
            qr = segno.make(tlv_data)
            out = qr.svg_data(scale=size // 25) if hasattr(qr, "svg_data") else None
            if out:
                return out
        except ImportError:
            pass

        # Priority 2: qrcode with SVGImage for SVG output
        try:
            import qrcode
            from qrcode.image.svg import SvgImage
            qr = qrcode.QRCode(box_size=size // 25, border=1)
            qr.add_data(tlv_data)
            img = qr.make_image(image_factory=SvgImage)
            import io
            buf = io.StringIO()
            img.save(buf)
            return buf.getvalue()
        except ImportError:
            pass

        # Priority 3: qrcode with Pillow for PNG output
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=size // 25, border=1)
            qr.add_data(tlv_data)
            img = qr.make_image()
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except ImportError:
            pass

        # Priority 4: Built-in fallback (visual-only, NOT ZATCA-compatible)
        from .svg_qr import SvgQrGenerator
        gen = SvgQrGenerator()
        svg = gen.generate(tlv_data, size)
        warning = (
            f'<text x="{size//2}" y="{size-5}" text-anchor="middle" '
            f'font-size="8" fill="red">'
            f"\u26a0 Install segno or qrcode[pil] for ZATCA-compatible QR</text>"
        )
        svg = svg.replace("</svg>", warning + "</svg>")
        return svg

    def render_as_base64(self, tlv_data, size=200):
        output = self.render(tlv_data, size)
        if isinstance(output, str):
            return base64.b64encode(output.encode("utf-8")).decode("ascii")
        return base64.b64encode(output).decode("ascii")

    def render_as_data_uri(self, tlv_data, size=200):
        output = self.render(tlv_data, size)
        if isinstance(output, str):
            b64 = base64.b64encode(output.encode("utf-8")).decode("ascii")
            return f"data:image/svg+xml;base64,{b64}"
        b64 = base64.b64encode(output).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def render_to_file(self, tlv_data, path, size=200):
        output = self.render(tlv_data, size)
        mode = "w" if isinstance(output, str) else "wb"
        with open(path, mode) as f:
            f.write(output)

    def render_html_svg(self, tlv_data, size=200):
        """Return SVG as an HTML-safe string, with warning if using fallback."""
        output = self.render(tlv_data, size)
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return output
