from django.test import TestCase
from django_zatca.services.svg_qr import SvgQrGenerator, _select_version, _rs_blocks


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

    def test_select_version_uses_rs_data_capacity(self):
        """_select_version must use RS block data capacity, not total codewords from VERSION_INFO."""
        from django_zatca.services.svg_qr import _get_max_data_length
        # v1 RS data = 19, VERSION_INFO[2] = 26. Data of 20 should NOT select v1 (can only hold 17 after overhead)
        self.assertNotEqual(_select_version(20), 1)
        # v1 max data length after overhead = 17
        self.assertEqual(_get_max_data_length(19, 1), 17)
        self.assertEqual(_select_version(17), 1)
        # v2 max data length after overhead = 32
        self.assertEqual(_get_max_data_length(34, 2), 32)
        self.assertEqual(_select_version(32), 2)

    def test_data_preserved_across_versions(self):
        """QR encode/decode must preserve all input data bytes."""
        gen = SvgQrGenerator()
        for size in range(1, 200):
            data = bytes([i % 256 for i in range(size)])
            tlv = b"\x01" + bytes([size]) + data
            try:
                svg = gen.generate(tlv)
                self.assertIn("<svg", svg, f"Failed for {size} bytes of data")
            except RuntimeError as e:
                self.fail(f"RuntimeError at {size} bytes: {e}")

    def test_encode_version_1_data_limit(self):
        """v1 has 19 data bytes via RS blocks, but 17 bytes after overhead."""
        v1_capacity = sum(b["data"] for b in _rs_blocks(1))
        self.assertEqual(v1_capacity, 19)
        from django_zatca.services.svg_qr import _get_max_data_length
        v1_max = _get_max_data_length(v1_capacity, 1)
        self.assertEqual(v1_max, 17)
        # 17 bytes fits in v1
        self.assertEqual(_select_version(17), 1)
        # 18 bytes requires v2
        self.assertEqual(_select_version(18), 2)
