from django import template
from django.utils.safestring import mark_safe
from django_zatca.services.qr_code import QRCodeService

register = template.Library()


@register.simple_tag
def zatca_qr(qr_data, size=200):
    """
    Render a ZATCA QR code as SVG.

    Usage:
        {% load zatca_qr %}
        {% zatca_qr qr_data size=200 %}

    Auto-detects available QR libraries:
      1. segno (recommended)
      2. qrcode with SVG writer
      3. qrcode with Pillow
      4. Built-in SvgQrGenerator (visual-only, shows warning)

    The output is marked safe for direct HTML embedding.
    """
    service = QRCodeService()
    svg = service.render_html_svg(qr_data, size=int(size))
    return mark_safe(svg)
