import sys
from Modules.type import PartInfo


def mkCombineFun(poly, initCrc=0, rev=True, xorOut=0):
    (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)

    mask = (int(1) << sizeBits) - 1
    if rev:
        poly = _bitrev(int(poly) & mask, sizeBits)
    else:
        poly = int(poly) & mask

    if sizeBits == 64:
        fun = _combine64
    else:
        raise NotImplemented

    def combine_fun(crc1, crc2, len2):
        return fun(poly, initCrc ^ xorOut, rev, xorOut, crc1, crc2, len2)

    return combine_fun


GF2_DIM = 64

def gf2_matrix_square(square, mat):
    for n in range(GF2_DIM):
        square[n] = gf2_matrix_times(mat, mat[n])


def gf2_matrix_times(mat, vec):
    summary = 0
    mat_index = 0

    while vec:
        if vec & 1:
            summary ^= mat[mat_index]

        vec >>= 1
        mat_index += 1

    return summary


def _combine64(poly, initCrc, rev, xorOut, crc1, crc2, len2):
    if len2 == 0:
        return crc1

    even = [0] * GF2_DIM
    odd = [0] * GF2_DIM

    crc1 ^= initCrc ^ xorOut

    if rev:
        # put operator for one zero bit in odd
        odd[0] = poly  # CRC-64 polynomial
        row = 1
        for n in range(1, GF2_DIM):
            odd[n] = row
            row <<= 1
    else:
        row = 2
        for n in range(0, GF2_DIM - 1):
            odd[n] = row
            row <<= 1
        odd[GF2_DIM - 1] = poly

    gf2_matrix_square(even, odd)

    gf2_matrix_square(odd, even)

    while True:
        gf2_matrix_square(even, odd)
        if len2 & int(1):
            crc1 = gf2_matrix_times(even, crc1)
        len2 >>= 1
        if len2 == 0:
            break

        gf2_matrix_square(odd, even)
        if len2 & int(1):
            crc1 = gf2_matrix_times(odd, crc1)
        len2 >>= 1

        if len2 == 0:
            break
    crc1 ^= crc2

    return crc1


def _verifyPoly(poly):
    msg = 'The degree of the polynomial must be 8, 16, 24, 32 or 64'
    poly = int(poly) # Use a common representation for all operations
    for n in (8, 16, 24, 32, 64):
        low = int(1) << n
        high = low*2
        if low <= poly < high:
            return n
    raise ValueError(msg)


def _bitrev(x, n):
    x = int(x)
    y = int(0)
    for i in range(n):
        y = (y << 1) | (x & int(1))
        x = x >> 1
    if ((int(1) << n)-1) <= sys.maxsize:
        return int(y)
    return y


def _verifyParams(poly, initCrc, xorOut):
    sizeBits = _verifyPoly(poly)

    mask = (int(1)<<sizeBits) - 1

    # Adjust the initial CRC to the correct data type (unsigned value).
    initCrc = int(initCrc) & mask
    if mask <= sys.maxsize:
        initCrc = int(initCrc)

    # Similar for XOR-out value.
    xorOut = int(xorOut) & mask
    if mask <= sys.maxsize:
        xorOut = int(xorOut)

    return (sizeBits, initCrc, xorOut)


class Crc64Combine:
    _POLY = 0x142F0E1EBA9EA3693
    _XOROUT = 0XFFFFFFFFFFFFFFFF

    def __init__(self):
        self.mkCombineFun = mkCombineFun(self._POLY, initCrc=0, rev=True, xorOut=self._XOROUT)

    def combine(self, crc1, crc2, len2):
        return self.mkCombineFun(crc1, crc2, len2)

    def calc_obj_crc_from_parts(self, parts: list[PartInfo, ...]):
        object_crc = 0
        for part in parts:
            object_crc = self.combine(object_crc, int(part.crc64), part.size)
        return str(object_crc)
