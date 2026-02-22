#!/usr/bin/env python3

STAR_COUNT = 20
REAL_INPUT = "VEGA-RIGL-DENB-ALTR-SIRI"
FAKE_INPUT = "NOVA-LYRA-ORIO-CYGN-ARCT"

REAL_ENC = bytes([
    0x37, 0xCD, 0x7A, 0x00, 0xC8, 0x09, 0x0D, 0xD2, 0x01,
    0x1E, 0xCE, 0x07, 0x1E, 0xAE, 0x03, 0x72, 0xE7,
])

FAKE_ENC = bytes([
    0x0E, 0xCC, 0x7D, 0x0A, 0xA9, 0x01, 0x13,
    0xCA, 0x05, 0x13, 0xAA, 0x01, 0x7F,
])


def rol32(v, r):
    return ((v << r) & 0xFFFFFFFF) | (v >> (32 - r))


def rol16(v, r):
    return ((v << r) & 0xFFFF) | (v >> (16 - r))


def flattenStars(text):
    if len(text) != 24:
        return None
    out = []
    for i, ch in enumerate(text):
        if i in (4, 9, 14, 19):
            if ch != "-":
                return None
            continue
        if not ("A" <= ch <= "Z"):
            return None
        out.append(ch)
    if len(out) != STAR_COUNT:
        return None
    return "".join(out)


def keyByte(i):
    keyWord = b"FALKEN"
    salt = bytes([0x0A, 0xDF, 0x01])
    return keyWord[i % 6] ^ salt[i % 3]


def xorDecrypt(enc):
    return bytes(b ^ keyByte(i) for i, b in enumerate(enc)).decode()


def crownReal(c):
    tags = [0x9720, 0xFB37, 0x8BC0, 0x6488, 0x48CF]
    ks = [0xFB6F, 0x931C, 0xBD97, 0x8756, 0x89CC]

    for g in range(5):
        raw = (ord(c[g * 4]) << 8) | ord(c[g * 4 + 1])
        mix = (ord(c[g * 4 + 2]) << 8) | ord(c[g * 4 + 3])
        calc = raw ^ rol16(mix, 3) ^ ks[g]
        if calc != tags[g]:
            return 0

    sig = 0x811C9DC5
    for i, ch in enumerate(c):
        sig ^= (ord(ch) + i * 13) & 0xFF
        sig = (sig * 0x01000193) & 0xFFFFFFFF
    sig ^= 0xAE88B2B5
    return sig


def mirrorReal(c):
    if ord(c[0]) + ord(c[19]) != 159:
        return 0, False
    if (ord(c[3]) ^ ord(c[12])) != 0:
        return 0, False
    if ((ord(c[4]) - 65) + (ord(c[5]) - 65) + (ord(c[6]) - 65)) % 26 != 5:
        return 0, False
    if ord(c[1]) - ord(c[8]) != 1:
        return 0, False
    if (ord(c[10]) ^ ord(c[14])) != 26:
        return 0, False
    if ord(c[7]) + ord(c[11]) + ord(c[15]) != 224:
        return 0, False

    sig = 0x9E3779B9
    for i, ch in enumerate(c):
        sig = rol32(sig ^ ((ord(ch) + i * 7) & 0xFF), 5)
        sig = (sig + 0x7F4A7C15 + (i * 0x1F123BB5)) & 0xFFFFFFFF
    return sig, True


def checkReal(text):
    c = flattenStars(text)
    if not c:
        return False
    sigA = crownReal(c)
    if sigA == 0:
        return False
    sigB, ok = mirrorReal(c)
    if not ok:
        return False
    return ((sigA ^ rol32(sigB, 7)) + 0x27D4EB2D) & 0xFFFFFFFF == 0x613283A6


def crownFake(c):
    tags = [0x09EB, 0xBE83, 0x553D, 0xCEA3, 0xFB4D]
    ks = [0x8F8E, 0xBAF0, 0x3386, 0x6432, 0xD097]

    for g in range(5):
        raw = (ord(c[g * 4]) << 8) | ord(c[g * 4 + 1])
        mix = (ord(c[g * 4 + 2]) << 8) | ord(c[g * 4 + 3])
        calc = raw ^ rol16(mix, 5) ^ ks[g]
        if calc != tags[g]:
            return 0

    sig = 0xA5B3571D
    for i, ch in enumerate(c):
        sig ^= ord(ch) * (i + 3)
        sig = rol32(sig, 9)
        sig = (sig + 0x10204081 + i * 0x1337) & 0xFFFFFFFF
    return sig


def mirrorFake(c):
    if ord(c[2]) + ord(c[17]) != 168:
        return 0, False
    if (ord(c[0]) ^ ord(c[19])) != 26:
        return 0, False
    if ((ord(c[4]) - 65) + (ord(c[9]) - 65) + (ord(c[13]) - 65)) % 26 != 0:
        return 0, False
    if ord(c[6]) - ord(c[1]) != 3:
        return 0, False
    if (ord(c[10]) ^ ord(c[14])) != 14:
        return 0, False
    if ord(c[3]) + ord(c[8]) + ord(c[12]) != 211:
        return 0, False

    sig = 0x6C8E9CF5
    for i, ch in enumerate(c):
        sig = (sig + ((ord(ch) ^ (i * 17)) & 0xFF) + 0x9D) & 0xFFFFFFFF
        sig = rol32(sig, (i % 11) + 3)
        sig ^= 0x7F4A9E21
    return sig, True


def checkFake(text):
    c = flattenStars(text)
    if not c:
        return False
    sigA = crownFake(c)
    if sigA == 0:
        return False
    sigB, ok = mirrorFake(c)
    if not ok:
        return False
    return ((sigA ^ rol32(sigB, 3)) + 0x31D9BEEF) & 0xFFFFFFFF == 0x628E1F60


def main():
    print("Real input:", REAL_INPUT)
    print("Real gate valid:", checkReal(REAL_INPUT))
    print("Real decrypt:", xorDecrypt(REAL_ENC))
    print()
    print("Fake input:", FAKE_INPUT)
    print("Fake gate valid:", checkFake(FAKE_INPUT))
    print("Fake decrypt:", xorDecrypt(FAKE_ENC))


if __name__ == "__main__":
    main()
