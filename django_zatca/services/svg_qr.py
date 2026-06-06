"""Pure-Python SVG QR Code generator (byte mode, Reed-Solomon, standard QR structure).

Port of the PHP SvgQrGenerator from the Laravel ZATCA package.
Supports QR versions 1-10 with byte encoding and L-level error correction.
"""

GF256_EXP = [
    1, 2, 4, 8, 16, 32, 64, 128, 29, 58, 116, 232, 205, 135, 19, 38,
    76, 152, 45, 90, 180, 117, 234, 201, 143, 3, 6, 12, 24, 48, 96, 192,
    157, 39, 78, 156, 37, 74, 148, 53, 106, 212, 181, 119, 238, 193, 159, 35,
    70, 140, 5, 10, 20, 40, 80, 160, 93, 186, 105, 210, 185, 111, 222, 161,
    95, 190, 97, 194, 153, 47, 94, 188, 101, 202, 137, 15, 30, 60, 120, 240,
    253, 231, 211, 187, 107, 214, 177, 127, 254, 225, 223, 163, 91, 182, 113, 226,
    217, 175, 67, 134, 17, 34, 68, 136, 13, 26, 52, 104, 208, 189, 103, 206,
    129, 31, 62, 124, 248, 237, 199, 147, 59, 118, 236, 197, 151, 51, 102, 204,
    133, 23, 46, 92, 184, 109, 218, 169, 79, 158, 33, 66, 132, 21, 42, 84,
    168, 77, 154, 41, 82, 164, 85, 170, 73, 146, 57, 114, 228, 213, 183, 115,
    230, 209, 191, 99, 198, 145, 63, 126, 252, 229, 215, 179, 123, 246, 241, 255,
    227, 219, 171, 75, 150, 49, 98, 196, 149, 55, 110, 220, 165, 87, 174, 65,
    130, 25, 50, 100, 200, 141, 7, 14, 28, 56, 112, 224, 221, 167, 83, 166,
    81, 162, 89, 178, 121, 242, 249, 239, 195, 155, 43, 86, 172, 69, 138, 9,
    18, 36, 72, 144, 61, 122, 244, 245, 247, 243, 251, 235, 203, 139, 11, 22,
    44, 88, 176, 125, 250, 233, 207, 131, 27, 54, 108, 216, 173, 71, 142, 1,
]

GF256_LOG = [
    -1, 0, 1, 25, 2, 50, 26, 198, 3, 223, 51, 238, 27, 104, 199, 75,
    4, 100, 224, 14, 52, 141, 239, 129, 28, 193, 105, 248, 200, 8, 76, 113,
    5, 138, 101, 47, 225, 36, 15, 33, 53, 147, 142, 218, 240, 18, 130, 69,
    29, 181, 194, 125, 106, 39, 249, 185, 201, 154, 9, 120, 77, 228, 114, 166,
    6, 191, 139, 98, 102, 221, 48, 253, 226, 152, 37, 179, 16, 145, 34, 136,
    54, 208, 148, 206, 143, 150, 219, 189, 241, 210, 19, 92, 131, 56, 70, 64,
    30, 66, 182, 163, 195, 72, 126, 110, 107, 58, 40, 84, 250, 133, 186, 61,
    202, 94, 155, 159, 10, 21, 121, 43, 78, 212, 229, 172, 115, 243, 167, 87,
    7, 112, 192, 247, 140, 128, 99, 13, 103, 74, 222, 237, 49, 197, 254, 24,
    227, 165, 153, 119, 38, 184, 180, 124, 17, 68, 146, 217, 35, 32, 137, 46,
    55, 63, 209, 91, 149, 188, 207, 205, 144, 135, 151, 178, 220, 252, 190, 97,
    242, 86, 211, 171, 20, 42, 93, 158, 132, 60, 57, 83, 71, 109, 65, 162,
    31, 45, 67, 216, 183, 123, 164, 118, 196, 23, 73, 236, 127, 12, 111, 246,
    108, 161, 59, 82, 41, 157, 85, 170, 251, 96, 134, 177, 187, 204, 62, 90,
    203, 89, 95, 176, 156, 169, 160, 81, 11, 245, 22, 235, 122, 117, 44, 215,
    79, 174, 213, 233, 230, 231, 173, 232, 116, 214, 244, 234, 168, 80, 88, 175,
]

VERSION_INFO = [
    (1, 21, 26, 18, 17, 14),
    (2, 25, 44, 34, 32, 28),
    (3, 29, 70, 56, 53, 44),
    (4, 33, 100, 80, 78, 64),
    (5, 37, 134, 108, 106, 86),
    (6, 41, 172, 136, 134, 108),
    (7, 45, 196, 156, 154, 124),
    (8, 49, 242, 194, 192, 154),
    (9, 53, 292, 232, 230, 182),
    (10, 57, 346, 274, 272, 216),
]


def _gf_poly_mul(a, b):
    res = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            if av and bv:
                res[i + j] ^= GF256_EXP[(GF256_LOG[av] + GF256_LOG[bv]) % 255]
    return res


def _reed_solomon(data, ec_count):
    gen = [1]
    for i in range(ec_count):
        gen = _gf_poly_mul(gen, [1, GF256_EXP[i]])
    msg = list(data) + [0] * ec_count
    for i in range(len(data)):
        if msg[i]:
            factor = GF256_LOG[msg[i]]
            for j in range(len(gen)):
                msg[i + j] ^= GF256_EXP[(factor + GF256_LOG[gen[j]]) % 255]
    return msg[len(data):]


def _rs_blocks(version):
    table = {
        1: (1, 26, 19, 7), 2: (1, 44, 34, 10), 3: (1, 70, 55, 15),
        4: (1, 100, 80, 20), 5: (1, 134, 108, 26), 6: (2, 86, 68, 18),
        7: (2, 98, 78, 20), 8: (2, 121, 97, 24), 9: (2, 146, 116, 30),
        10: (2, 86, 68, 18),
    }
    num_blocks, _, data, ec = table.get(version, (1, 100, 80, 20))
    return [{"data": data, "ec": ec} for _ in range(num_blocks)]


def _get_max_data_length(total_data_bytes, version):
    """Max bytes of actual data that fit, accounting for mode + count overhead."""
    char_count_bits = 8 if version < 10 else 16
    overhead_bits = 4 + char_count_bits
    max_data_bits = (total_data_bytes * 8) - overhead_bits
    return max_data_bits // 8


def _select_version(data_len):
    for v in range(1, 11):
        capacity = sum(b["data"] for b in _rs_blocks(v))
        if data_len <= _get_max_data_length(capacity, v):
            return v
    return 10


class SvgQrGenerator:
    def generate(self, data, output_size=200):
        version = _select_version(len(data))
        size = VERSION_INFO[version - 1][1]
        matrix = [[-1] * size for _ in range(size)]

        self._place_finders(matrix, size)
        self._place_timing(matrix, size)
        self._place_alignments(matrix, size, version)
        self._place_format_reserved(matrix, size)

        encoded = self._encode_data(data, version)
        self._place_data(matrix, encoded, size)

        mask = self._select_mask(matrix, size)
        self._apply_mask(matrix, mask, size)
        self._place_format_info(matrix, mask, size)
        self._place_version_info(matrix, version, size)

        return self._render_svg(matrix, output_size)

    def _place_finders(self, matrix, size):
        for x, y in [(0, 0), (size - 7, 0), (0, size - 7)]:
            self._draw_finder(matrix, x, y, size)

    def _draw_finder(self, matrix, x, y, size):
        for r in range(-1, 8):
            for c in range(-1, 8):
                px, py = x + c, y + r
                if px < 0 or px >= size or py < 0 or py >= size:
                    continue
                if 0 <= r <= 7 and 0 <= c <= 7:
                    on = (r == 0 or r == 6 or c == 0 or c == 6) or (2 <= r <= 4 and 2 <= c <= 4)
                    matrix[py][px] = 1 if on else 0
                else:
                    matrix[py][px] = 0

    def _place_timing(self, matrix, size):
        for i in range(8, size - 8):
            matrix[6][i] = 1 if i % 2 == 0 else 0
            matrix[i][6] = 1 if i % 2 == 0 else 0

    def _place_alignments(self, matrix, size, version):
        positions = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
                     6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
        pos = positions.get(version, [])
        for py in pos:
            for px in pos:
                if matrix[py][px] != -1:
                    continue
                for r in range(-2, 3):
                    for c in range(-2, 3):
                        xx, yy = px + c, py + r
                        if 0 <= xx < size and 0 <= yy < size:
                            on = (abs(r) == 2 or abs(c) == 2) or (r == 0 and c == 0)
                            matrix[yy][xx] = 1 if on else 0

    def _place_format_reserved(self, matrix, size):
        for i in range(9):
            if i != 6:
                matrix[8][i] = 0
                matrix[i][8] = 0
        for i in range(size - 8, size):
            matrix[8][i] = 0
        for i in range(size - 7, size):
            matrix[i][8] = 0
        matrix[size - 8][8] = 1

    def _encode_data(self, data, version):
        mode = 0b0100
        char_count = len(data)
        blocks = _rs_blocks(version)
        total_data_bytes = sum(b["data"] for b in blocks)
        total_bits = total_data_bytes * 8
        char_count_bits = 8 if version < 10 else 16

        bits = []
        self._append_bits(bits, mode, 4)
        self._append_bits(bits, char_count, char_count_bits)

        for ch in data:
            if isinstance(ch, int):
                self._append_bits(bits, ch, 8)
            else:
                self._append_bits(bits, ord(ch), 8)

        if len(bits) > total_bits:
            raise RuntimeError(f"Data too long for version {version}")

        self._append_bits(bits, 0, min(4, total_bits - len(bits)))
        while len(bits) % 8:
            bits.append(0)

        ba = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte = (byte << 1) | bits[i + j]
            ba.append(byte)

        pad = [236, 17]
        pi = 0
        while len(ba) < total_data_bytes:
            ba.append(pad[pi % 2])
            pi += 1

        data_chunks = []
        ec_chunks = []
        remaining = list(ba)
        for blk in blocks:
            chunk = remaining[:blk["data"]]
            remaining = remaining[blk["data"]:]
            data_chunks.append(chunk)
            ec_chunks.append(_reed_solomon(chunk, blk["ec"]))

        interleaved = []
        max_data = max(b["data"] for b in blocks)
        for i in range(max_data):
            for bi, blk in enumerate(blocks):
                if i < blk["data"]:
                    offset = sum(blocks[j]["data"] for j in range(bi))
                    idx = offset + i
                    if idx < len(ba):
                        interleaved.append(ba[idx])
        interleaved.extend([b for chunk in ec_chunks for b in chunk])
        return interleaved

    def _append_bits(self, bits, value, num_bits):
        for i in range(num_bits - 1, -1, -1):
            bits.append((value >> i) & 1)

    def _place_data(self, matrix, data_bytes, size):
        bit_idx = 0
        total_bits = len(data_bytes) * 8
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for row in range(size):
                for col in range(2):
                    x = right - col
                    y = (size - 1 - row) if (right % 2 == 0) else row
                    if y < 0 or y >= size or x < 0 or x >= size:
                        continue
                    if matrix[y][x] != -1:
                        continue
                    if bit_idx < total_bits:
                        byte_idx = bit_idx // 8
                        bit_pos = 7 - (bit_idx % 8)
                        matrix[y][x] = (data_bytes[byte_idx] >> bit_pos) & 1
                        bit_idx += 1
                    else:
                        matrix[y][x] = 0
            right -= 2

    def _get_mask_bit(self, mask, x, y):
        return {
            0: (y + x) % 2 == 0,
            1: y % 2 == 0,
            2: x % 3 == 0,
            3: (y + x) % 3 == 0,
            4: ((y // 2) + (x // 3)) % 2 == 0,
            5: (y * x) % 2 + (y * x) % 3 == 0,
            6: ((y * x) % 2 + (y * x) % 3) % 2 == 0,
            7: ((y * x) % 3 + (y + x) % 2) % 2 == 0,
        }.get(mask, False)

    def _apply_mask(self, matrix, mask, size):
        for y in range(size):
            for x in range(size):
                if matrix[y][x] in (0, 1):
                    if self._get_mask_bit(mask, x, y):
                        matrix[y][x] ^= 1

    def _evaluate_mask(self, matrix, mask, size):
        score = 0
        cloned = [row[:] for row in matrix]
        self._apply_mask(cloned, mask, size)

        for row in cloned:
            run, prev, adj = 0, -1, 0
            for val in row:
                if val in (0, 1):
                    if val == prev:
                        run += 1
                    else:
                        if run >= 5:
                            score += run + 2
                        run, prev = 1, val
                else:
                    if run >= 5:
                        score += run + 2
                    run, prev = 0, -1
            if run >= 5:
                score += run + 2

        for x in range(size):
            run, prev = 0, -1
            for y in range(size):
                val = cloned[y][x]
                if val in (0, 1):
                    if val == prev:
                        run += 1
                    else:
                        if run >= 5:
                            score += run + 2
                        run, prev = 1, val
                else:
                    if run >= 5:
                        score += run + 2
                    run, prev = 0, -1
            if run >= 5:
                score += run + 2

        blocks = size // 2
        bcount = 0
        for y in range(blocks):
            for x in range(blocks):
                vals = [cloned[y * 2 + dy][x * 2 + dx] for dy in range(2) for dx in range(2)]
                if all(v is not None and v == vals[0] for v in vals):
                    bcount += 1
        score += bcount * 3

        dark = sum(1 for row in cloned for val in row if val == 1)
        total = sum(1 for row in cloned for val in row if val in (0, 1))
        if total:
            pct = (dark * 100) // total
            prev = (pct // 5) * 5
            nxt = prev + 5
            score += min(abs(prev - 50) * 2, abs(nxt - 50) * 2)

        return score

    def _select_mask(self, matrix, size):
        best, best_score = 0, float("inf")
        for m in range(8):
            s = self._evaluate_mask(matrix, m, size)
            if s < best_score:
                best, best_score = m, s
        return best

    def _place_format_info(self, matrix, mask, size):
        ec_level = 0b01
        fmt = (ec_level << 3) | mask
        gen = 0b10100110111
        data = fmt << 10
        for i in range(14, 9, -1):
            if (data >> i) & 1:
                data ^= gen << (i - 10)
        fmt_data = ((fmt << 10) | data) ^ 0b101010000010010

        positions = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(i, 8) for i in range(5, -1, -1)]
        positions += [(size - 1 - i, 8) for i in range(8)] + [(8, size - 8)] + [(8, i) for i in range(size - 7, size - 1)]
        dark = (size - 8, 8)

        for i, (xx, yy) in enumerate(positions):
            if (yy, xx) == dark:
                continue
            if i < 15 and 0 <= yy < size and 0 <= xx < size:
                matrix[yy][xx] = (fmt_data >> (14 - i)) & 1
        matrix[dark[0]][dark[1]] = 1

    def _place_version_info(self, matrix, version, size):
        if version < 7:
            return
        data = version
        gen = 0b1111101001010
        bits = data << 12
        for i in range(17, 11, -1):
            if (bits >> i) & 1:
                bits ^= gen << (i - 12)
        vbits = (data << 12) | bits
        for r in range(6):
            for c in range(3):
                for xx, yy in [(size - 11 + c, r), (r, size - 11 + c)]:
                    idx = r * 3 + c
                    if idx < 18 and xx < size and yy < size:
                        matrix[yy][xx] = (vbits >> (17 - idx)) & 1

    def _render_svg(self, matrix, output_size):
        size = len(matrix)
        svg = [f'<svg width="{output_size}" height="{output_size}" viewBox="0 0 {size} {size}"'
               f' xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">']
        svg.append(f'<rect width="{size}" height="{size}" fill="#ffffff"/>')
        dark, light = "", ""
        for y in range(size):
            for x in range(size):
                if matrix[y][x] in (0, 1):
                    module = f"M{x} {y}h1v1h-1z"
                    if matrix[y][x] == 1:
                        dark += module
                    else:
                        light += module
        if dark:
            svg.append(f'<path fill="#000000" d="{dark}"/>')
        if light:
            svg.append(f'<path fill="#ffffff" d="{light}"/>')
        svg.append("</svg>")
        return "".join(svg)
