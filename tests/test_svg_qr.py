from django.test import TestCase
from django_zatca.services.svg_qr import SvgQrGenerator


class SvgQrGeneratorTestCase(TestCase):
    def test_generate_basic(self):
        gen = SvgQrGenerator()
        tlv = b"\x01\x05Hello\x02\x03VAT"
        svg = gen.generate(tlv)
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)

    def test_generate_big_bang(self):
        gen = SvgQrGenerator()
        import struct
        tlv = b""
        for tag, val in [(1, b"Test Company SAR"), (2, b"311111111100003"),
                         (3, b"2024-01-15T14:30:00Z"), (4, b"115.00"), (5, b"15.00")]:
            tlv += struct.pack(">B", tag) + struct.pack(">B", len(val)) + val
        svg = gen.generate(tlv)
        self.assertIn("<svg", svg)
        self.assertGreater(len(svg), 500)

    def test_multiple_calls(self):
        gen = SvgQrGenerator()
        svg1 = gen.generate(b"\x01\x02AB")
        svg2 = gen.generate(b"\x01\x02CD")
        self.assertIn("<svg", svg1)
        self.assertIn("<svg", svg2)

    def test_custom_output_size(self):
        gen = SvgQrGenerator()
        svg = gen.generate(b"\x01\x02XY", output_size=300)
        self.assertIn('width="300"', svg)
